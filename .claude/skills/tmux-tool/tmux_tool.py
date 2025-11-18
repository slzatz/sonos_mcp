#!/home/slzatz/sonos_mcp/.venv/bin/python3
"""
tmux Tool Dispatcher for Direct Mode

Exposes tmux operations as discrete command-line tools for TUI interaction.
Usage: tmux_tool.py <tool_name> [args...]

Provides 6 tools optimized for TUI workflows:
- find_session, create_session, get_pane (session management)
- capture_pane, send_keys (TUI interaction)
- session_ready (convenience: all-in-one setup)

Adapted from tmux-mcp server (https://github.com/nickgnd/tmux-mcp)
"""

import sys
import subprocess


def execute_tmux(command: str) -> str:
    """
    Execute a tmux command and return stdout.

    Args:
        command: tmux command string (without 'tmux' prefix)

    Returns:
        Command output (stdout), stripped

    Raises:
        Exception: If tmux command fails

    Pattern borrowed from tmux-mcp tmux.ts:58-65
    """
    try:
        result = subprocess.run(
            f"tmux {command}",
            shell=True,  # Needed for complex quoting
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Include both stderr and stdout in error for debugging
        error_msg = e.stderr.strip() if e.stderr else e.stdout.strip()
        raise Exception(f"tmux command failed: {error_msg}")
    except subprocess.TimeoutExpired:
        raise Exception("tmux command timed out after 5 seconds")


def handle_error(e: Exception, tool_name: str) -> str:
    """Standardized error handling for all tools."""
    error_msg = f"Error in {tool_name}: {str(e)}"
    print(error_msg, file=sys.stderr)
    return error_msg


# Tool registry: Maps tool names to handler functions
TOOLS = {}


def tool(name):
    """Decorator to register tools."""
    def decorator(func):
        TOOLS[name] = func
        return func
    return decorator


# Session Management Tools

@tool("find_session")
def find_session(args):
    """
    Check if tmux session exists by name.

    Args:
        session_name (required): Name of session to find

    Returns:
        Session info if found, or "not found" message

    Pattern borrowed from tmux-mcp tmux.ts:102-109
    """
    if len(args) < 3:
        return "Error: session_name required"

    name = args[2]

    try:
        # Check if session exists (has-session returns exit code 0 if exists)
        execute_tmux(f"has-session -t '{name}'")

        # Get session details using format string
        # Pattern from tmux-mcp tmux.ts:83
        output = execute_tmux(
            f"list-sessions -F '#{{session_id}}:#{{session_name}}:#{{session_windows}}'"
        )

        # Find the matching session
        for line in output.split('\n'):
            parts = line.split(':')
            if len(parts) >= 2 and parts[1] == name:
                session_id = parts[0]
                session_name = parts[1]
                windows = parts[2] if len(parts) > 2 else 'unknown'
                return f"Session found: {session_name} (ID: {session_id}, Windows: {windows})"

        return f"Session '{name}' exists"

    except Exception:
        return f"Session '{name}' not found"


@tool("create_session")
def create_session(args):
    """
    Create a new tmux session (detached).

    Args:
        session_name (required): Name for new session

    Returns:
        Success confirmation or error

    Pattern borrowed from tmux-mcp tmux.ts:162-165
    """
    if len(args) < 3:
        return "Error: session_name required"

    name = args[2]

    try:
        # Create detached session
        execute_tmux(f"new-session -d -s '{name}'")

        # Verify it was created
        verify = execute_tmux(f"list-sessions -F '{{session_name}}' | grep '^{name}$'")

        if verify:
            return f"Session '{name}' created successfully"
        else:
            return f"Session '{name}' created (verification unclear)"

    except Exception as e:
        # Check if session already exists
        if "duplicate session" in str(e).lower():
            return f"Session '{name}' already exists"
        return handle_error(e, "create_session")


@tool("get_pane")
def get_pane(args):
    """
    Get pane ID for session (auto-creates session if doesn't exist).

    Args:
        session_name (required): Name of session

    Returns:
        Pane ID (e.g., "%0") or error

    Pattern borrowed from tmux-mcp tmux.ts:134-149 (listPanes)
    """
    if len(args) < 3:
        return "Error: session_name required"

    name = args[2]

    try:
        # Check if session exists, create if not
        try:
            execute_tmux(f"has-session -t '{name}'")
        except Exception:
            # Session doesn't exist, create it
            execute_tmux(f"new-session -d -s '{name}'")

        # Get pane ID for session
        # Pattern: list panes and get first one (there's always at least one)
        output = execute_tmux(f"list-panes -t '{name}' -F '#{{pane_id}}'")

        if output:
            # Return first pane ID
            pane_id = output.split('\n')[0]
            return pane_id
        else:
            return f"Error: No panes found in session '{name}'"

    except Exception as e:
        return handle_error(e, "get_pane")


# TUI Interaction Tools

@tool("capture_pane")
def capture_pane(args):
    """
    Capture content from a tmux pane.

    Args:
        pane_id (required): Pane ID (e.g., "%0")
        lines (optional): Number of lines to capture (default: 40)

    Returns:
        Pane content (text) or error

    Pattern borrowed from tmux-mcp tmux.ts:154-157
    """
    if len(args) < 3:
        return "Error: pane_id required"

    pane_id = args[2]
    lines = int(args[3]) if len(args) >= 4 else 40

    try:
        # Capture pane content
        # -p: print to stdout
        # -S -N: start N lines back from end
        # -E -: end at last line
        # Pattern from tmux-mcp tmux.ts:156
        output = execute_tmux(f"capture-pane -p -t '{pane_id}' -S -{lines} -E -")

        return output if output else "No content captured"

    except Exception as e:
        return handle_error(e, "capture_pane")


@tool("send_keys")
def send_keys(args):
    """
    Send keystrokes to a tmux pane.

    Args:
        pane_id (required): Pane ID (e.g., "%0")
        text (required): Text to send
        enter (optional): Press Enter after text (default: "true")

    Returns:
        Success confirmation or error

    Pattern borrowed from tmux-mcp tmux.ts:284 (with quote escaping)
    """
    if len(args) < 4:
        return "Error: pane_id and text required"

    pane_id = args[2]
    text = args[3]
    press_enter = True

    if len(args) >= 5:
        enter_arg = args[4].lower()
        press_enter = enter_arg not in ['false', 'no', '0']

    try:
        # Escape single quotes in text
        # Pattern from tmux-mcp tmux.ts:284
        # ' becomes '\'' (end quote, escaped quote, start quote)
        escaped_text = text.replace("'", "'\\''")

        # Build command with optional Enter key
        enter_key = " Enter" if press_enter else ""

        # Send keys to pane
        execute_tmux(f"send-keys -t '{pane_id}' '{escaped_text}'{enter_key}")

        return f"Keys sent to pane {pane_id}"

    except Exception as e:
        return handle_error(e, "send_keys")


# Convenience Tools

@tool("session_ready")
def session_ready(args):
    """
    Ensure session exists and return pane ID (all-in-one setup).

    This is a convenience tool that combines find_session, create_session,
    and get_pane into a single operation.

    Args:
        session_name (required): Name of session

    Returns:
        Pane ID ready for use, or error
    """
    if len(args) < 3:
        return "Error: session_name required"

    name = args[2]

    try:
        # Check if session exists, create if not
        try:
            execute_tmux(f"has-session -t '{name}'")
            session_status = "existing"
        except Exception:
            # Create new session
            execute_tmux(f"new-session -d -s '{name}'")
            session_status = "created"

        # Get pane ID
        output = execute_tmux(f"list-panes -t '{name}' -F '#{{pane_id}}'")

        if output:
            pane_id = output.split('\n')[0]
            return f"Session '{name}' {session_status}. Pane ready: {pane_id}"
        else:
            return f"Error: Session '{name}' {session_status} but no pane found"

    except Exception as e:
        return handle_error(e, "session_ready")


def main():
    """Main dispatcher entry point."""
    if len(sys.argv) < 2:
        print("Usage: tmux_tool.py <tool_name> [args...]", file=sys.stderr)
        print(f"\nAvailable tools ({len(TOOLS)}):", file=sys.stderr)
        for tool_name in sorted(TOOLS.keys()):
            print(f"  {tool_name}", file=sys.stderr)
        sys.exit(1)

    tool_name = sys.argv[1]

    if tool_name not in TOOLS:
        print(f"Error: Unknown tool '{tool_name}'", file=sys.stderr)
        print(f"\nAvailable tools ({len(TOOLS)}):", file=sys.stderr)
        for name in sorted(TOOLS.keys()):
            print(f"  {name}", file=sys.stderr)
        sys.exit(1)

    # Execute tool
    try:
        result = TOOLS[tool_name](sys.argv)
        print(result)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
