#!/home/slzatz/sonos_mcp/.venv/bin/python3
"""
Sonos Tool Dispatcher for Direct Mode

Exposes sonos_actions functions as discrete command-line tools.
Usage: sonos_tool.py <tool_name> [args...]

This dispatcher provides 23 active tools (19 Sonos + 4 TUI lifecycle),
matching MCP functionality but executing directly for token efficiency.
"""

import sys
import json
import os
import subprocess
import signal
import time
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sonos import sonos_actions


def initialize_speaker():
    """Ensure speaker is initialized before operations."""
    try:
        sonos_actions.set_master()
    except Exception as e:
        print(f"Error initializing speaker: {e}", file=sys.stderr)
        sys.exit(1)


def handle_error(e: Exception, tool_name: str):
    """Standardized error handling for all tools."""
    error_msg = f"Error in {tool_name}: {str(e)}"
    print(error_msg, file=sys.stderr)
    return error_msg


# Tool registry: Maps tool names to (function, arg_parser) tuples
# arg_parser is a function that takes sys.argv and returns args for the sonos_actions function
TOOLS = {}


def tool(name):
    """Decorator to register tools."""
    def decorator(func):
        TOOLS[name] = func
        return func
    return decorator


# Speaker Management Tools

@tool("get_master_speaker")
def get_master_speaker(args):
    """Get the currently configured master speaker name."""
    # Try to initialize if not already done
    if not hasattr(sonos_actions, 'master') or sonos_actions.master is None:
        sonos_actions.set_master()

    if sonos_actions.master:
        return f"Current master speaker: {sonos_actions.master.player_name}"
    return "No speaker connected"


@tool("set_master_speaker")
def set_master_speaker(args):
    """Change the master speaker to a different Sonos device."""
    if len(args) < 3:
        return "Error: speaker_name required"
    speaker_name = args[2]
    try:
        sonos_actions.set_master(speaker_name)
        return f"Successfully changed master speaker to {speaker_name}"
    except Exception as e:
        return handle_error(e, "set_master_speaker")


# Music Search Tools
# Use tmux and sonos_interactive_tui for all searches
#@tool("search_for_track")
#def search_for_track(args):
#    """Search for music tracks by title, artist, or both."""
#    if len(args) < 3:
#        return "Error: query required"
#    query = args[2]
#    try:
#        return sonos_actions.search_for_track(query)
#    except Exception as e:
#        return handle_error(e, "search_for_track")
#
#
#@tool("search_for_album")
#def search_for_album(args):
#    """Search for music albums by title or artist."""
#    if len(args) < 3:
#        return "Error: query required"
#    query = args[2]
#    try:
#        return sonos_actions.search_for_album(query)
#    except Exception as e:
#        return handle_error(e, "search_for_album")
#

# Queue Management Tools

@tool("list_queue")
def list_queue(args):
    """Display the current Sonos queue showing all queued tracks."""
    try:
        result = sonos_actions.list_queue()
        if isinstance(result, list):
            # Format as numbered list
            if not result:
                return "Queue is empty"
            output = []
            for i, track in enumerate(result, 1):
                title = track.get('title', 'Unknown')
                artist = track.get('artist', 'Unknown')
                album = track.get('album', 'Unknown')
                output.append(f"{i}. {title} - {artist} - {album}")
            return "\n".join(output)
        return str(result)
    except Exception as e:
        return handle_error(e, "list_queue")


@tool("add_track_to_queue")
def add_track_to_queue(args):
    """Add a track from search results to the queue by position number."""
    if len(args) < 3:
        return "Error: position required"
    try:
        position = int(args[2])
        result = sonos_actions.add_track_to_queue(position)
        return result if result else f"Added track {position} to queue"
    except ValueError:
        return "Error: position must be an integer"
    except Exception as e:
        return handle_error(e, "add_track_to_queue")


@tool("add_album_to_queue")
def add_album_to_queue(args):
    """Add an album from search results to the queue by position number."""
    if len(args) < 3:
        return "Error: position required"
    try:
        position = int(args[2])
        result = sonos_actions.add_album_to_queue(position)
        return result if result else f"Added album {position} to queue"
    except ValueError:
        return "Error: position must be an integer"
    except Exception as e:
        return handle_error(e, "add_album_to_queue")


@tool("clear_queue")
def clear_queue(args):
    """Clear all tracks from the current queue."""
    try:
        sonos_actions.clear_queue()
        return "Queue cleared"
    except Exception as e:
        return handle_error(e, "clear_queue")


@tool("remove_from_queue")
def remove_from_queue(args):
    """Remove a track from the queue by its position number."""
    if len(args) < 3:
        return "Error: position required"
    try:
        position = int(args[2])
        result = sonos_actions.remove_from_queue(position)
        return result if result else f"Removed track {position} from queue"
    except ValueError:
        return "Error: position must be an integer"
    except Exception as e:
        return handle_error(e, "remove_from_queue")


@tool("play_from_queue")
def play_from_queue(args):
    """Play a track from the queue by its position number (1-indexed)."""
    if len(args) < 3:
        return "Error: position required"
    try:
        position = int(args[2])

        # Validate position is positive
        if position < 1:
            return "Error: position must be a positive number (1 or greater)"

        # Get queue to validate position
        queue = sonos_actions.list_queue()
        if position > len(queue):
            return f"Error: position {position} is out of range. Queue has {len(queue)} tracks."

        # Convert from 1-indexed (user-friendly) to 0-indexed (SoCo internal)
        result = sonos_actions.play_from_queue(position - 1)
        return result if result else f"Now playing track {position} from queue"
    except ValueError:
        return "Error: position must be an integer"
    except Exception as e:
        return handle_error(e, "play_from_queue")


# Playback Control Tools

@tool("current_track")
def current_track(args):
    """Get information about what's currently playing."""
    try:
        result = sonos_actions.current_track_info(text=True)
        return result if result else "No track currently playing"
    except Exception as e:
        return handle_error(e, "current_track")


@tool("play_pause")
def play_pause(args):
    """Toggle play/pause of the current track."""
    try:
        result = sonos_actions.play_pause()
        return result if result else "Toggled play/pause"
    except Exception as e:
        return handle_error(e, "play_pause")


@tool("next_track")
def next_track(args):
    """Skip to the next track in the queue."""
    try:
        result = sonos_actions.playback('next')
        return result if result else "Playing next track"
    except Exception as e:
        return handle_error(e, "next_track")


# Volume Control Tools

@tool("turn_volume")
def turn_volume(args):
    """Adjust volume up or down by 10."""
    if len(args) < 3:
        return "Error: direction required (louder/quieter)"
    direction = args[2].lower()
    if direction not in ['louder', 'quieter']:
        return "Error: direction must be 'louder' or 'quieter'"
    try:
        result = sonos_actions.turn_volume(direction)
        return result if result else f"Volume adjusted {direction}"
    except Exception as e:
        return handle_error(e, "turn_volume")


@tool("set_volume")
def set_volume(args):
    """Set the absolute volume level (0-100)."""
    if len(args) < 3:
        return "Error: level required (0-100)"
    try:
        level = int(args[2])
        if not 0 <= level <= 100:
            return "Error: level must be between 0 and 100"
        result = sonos_actions.set_volume(level)
        return result if result else f"Volume set to {level}"
    except ValueError:
        return "Error: level must be an integer"
    except Exception as e:
        return handle_error(e, "set_volume")


@tool("mute")
def mute(args):
    """Mute or unmute all speakers in the group."""
    if len(args) < 3:
        return "Error: muted state required (true/false)"
    muted_str = args[2].lower()
    if muted_str not in ['true', 'false']:
        return "Error: muted must be 'true' or 'false'"
    muted = muted_str == 'true'
    try:
        result = sonos_actions.mute(muted)
        status = "Muted" if muted else "Unmuted"
        return result if result else status
    except Exception as e:
        return handle_error(e, "mute")


# Playlist Management Tools

@tool("list_playlists")
def list_playlists(args):
    """List all available local playlists."""
    try:
        result = sonos_actions.list_playlists()
        return result if result else "No playlists found"
    except Exception as e:
        return handle_error(e, "list_playlists")


@tool("add_to_playlist_from_queue")
def add_to_playlist_from_queue(args):
    """Add a track from the queue to a playlist."""
    if len(args) < 4:
        return "Error: playlist and position required"
    playlist = args[2]
    try:
        position = int(args[3])
        result = sonos_actions.add_to_playlist_from_queue(playlist, position)
        return result if result else f"Added track {position} to playlist {playlist}"
    except ValueError:
        return "Error: position must be an integer"
    except Exception as e:
        return handle_error(e, "add_to_playlist_from_queue")


@tool("add_to_playlist_from_search")
def add_to_playlist_from_search(args):
    """Add a track from search results to a playlist."""
    if len(args) < 4:
        return "Error: playlist and position required"
    playlist = args[2]
    try:
        position = int(args[3])
        result = sonos_actions.add_to_playlist_from_search(playlist, position)
        return result if result else f"Added search result {position} to playlist {playlist}"
    except ValueError:
        return "Error: position must be an integer"
    except Exception as e:
        return handle_error(e, "add_to_playlist_from_search")


@tool("add_playlist_to_queue")
def add_playlist_to_queue(args):
    """Load a playlist to the queue."""
    if len(args) < 3:
        return "Error: playlist name required"
    playlist = args[2]
    # Check for optional shuffle parameter
    shuffle = False
    if len(args) >= 4:
        shuffle_str = args[3].lower()
        if shuffle_str in ['true', 'false']:
            shuffle = shuffle_str == 'true'
        else:
            return "Error: shuffle must be 'true' or 'false'"
    try:
        result = sonos_actions.add_playlist_to_queue(playlist, shuffle)
        shuffle_msg = " (shuffled)" if shuffle else ""
        return result if result else f"Added playlist {playlist} to queue{shuffle_msg}"
    except Exception as e:
        return handle_error(e, "add_playlist_to_queue")


@tool("list_playlist_tracks")
def list_playlist_tracks(args):
    """Display all tracks in a saved playlist."""
    if len(args) < 3:
        return "Error: playlist name required"
    playlist = args[2]
    try:
        # Read playlist file directly
        playlist_path = Path.home() / ".sonos" / "playlists" / f"{playlist}.json"
        if not playlist_path.exists():
            return f"Playlist '{playlist}' not found"

        with open(playlist_path) as f:
            tracks = json.load(f)

        if not tracks:
            return f"Playlist '{playlist}' is empty"

        output = [f"Playlist '{playlist}' ({len(tracks)} tracks):"]
        for i, track in enumerate(tracks, 1):
            title = track.get('title', 'Unknown')
            artist = track.get('artist', 'Unknown')
            album = track.get('album', 'Unknown')
            output.append(f"{i}. {title} - {artist} - {album}")
        return "\n".join(output)
    except Exception as e:
        return handle_error(e, "list_playlist_tracks")


@tool("remove_track_from_playlist")
def remove_track_from_playlist(args):
    """Remove a track from a playlist by position."""
    if len(args) < 4:
        return "Error: playlist and position required"
    playlist = args[2]
    try:
        position = int(args[3])
        # Read, modify, write playlist
        playlist_path = Path.home() / ".sonos" / "playlists" / f"{playlist}.json"
        if not playlist_path.exists():
            return f"Playlist '{playlist}' not found"

        with open(playlist_path) as f:
            tracks = json.load(f)

        if position < 1 or position > len(tracks):
            return f"Error: position must be between 1 and {len(tracks)}"

        removed = tracks.pop(position - 1)

        with open(playlist_path, 'w') as f:
            json.dump(tracks, f, indent=2)

        title = removed.get('title', 'Unknown')
        return f"Removed '{title}' from playlist {playlist}"
    except ValueError:
        return "Error: position must be an integer"
    except Exception as e:
        return handle_error(e, "remove_track_from_playlist")


@tool("list_native_sonos_playlists")
def list_native_sonos_playlists(args):
    """List all native Sonos playlists stored on the Sonos system."""
    try:
        result = sonos_actions.get_native_sonos_playlists()
        return result if result else "No native Sonos playlists found"
    except Exception as e:
        return handle_error(e, "list_native_sonos_playlists")


@tool("create_native_sonos_playlist_from_local")
def create_native_sonos_playlist_from_local(args):
    """Create a native Sonos playlist from a local playlist file."""
    if len(args) < 3:
        return "Error: local_playlist name required"
    local_playlist = args[2]
    native_playlist_name = args[3] if len(args) >= 4 else None
    try:
        result = sonos_actions.create_native_playlist_from_local(
            local_playlist, native_playlist_name
        )
        return result if result else f"Created native Sonos playlist from {local_playlist}"
    except Exception as e:
        return handle_error(e, "create_native_sonos_playlist_from_local")


# TUI Lifecycle Management Tools

@tool("tui_status")
def tui_status(args):
    """Check TUI running status and current state."""
    try:
        state_file = Path.home() / ".sonos" / "tui_state.json"

        # Check if state file exists
        if not state_file.exists():
            return json.dumps({
                "running": False,
                "status": "not_running",
                "message": "TUI not running (no state file found)"
            }, indent=2)

        # Read state file
        with open(state_file) as f:
            state = json.load(f)

        # Check if status is already "stopped"
        if state.get("status") == "stopped":
            return json.dumps({
                "running": False,
                "status": "stopped",
                "message": "TUI is stopped"
            }, indent=2)

        # Verify process is actually running
        pid = state.get("pid")
        if pid:
            try:
                # Check if process exists (os.kill with signal 0 doesn't kill, just checks)
                os.kill(pid, 0)
                process_alive = True
            except (OSError, ProcessLookupError):
                process_alive = False
        else:
            process_alive = False

        # Verify tmux pane exists
        pane_id = state.get("pane_id", "unknown")
        pane_alive = False
        if pane_id != "unknown":
            try:
                result = subprocess.run(
                    ["tmux", "list-panes", "-a", "-F", "#{pane_id}"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                pane_alive = pane_id in result.stdout
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pane_alive = False

        # Determine final status
        if process_alive and pane_alive:
            return json.dumps({
                "running": True,
                "status": state.get("status", "running"),
                "current_prompt": state.get("current_prompt", "unknown"),
                "pid": pid,
                "pane_id": pane_id,
                "last_updated": state.get("last_updated", "unknown")
            }, indent=2)
        else:
            return json.dumps({
                "running": False,
                "status": "stale",
                "message": f"TUI state file exists but process/pane not found (process_alive={process_alive}, pane_alive={pane_alive})",
                "pid": pid,
                "pane_id": pane_id
            }, indent=2)

    except Exception as e:
        return handle_error(e, "tui_status")


@tool("tui_start")
def tui_start(args):
    """Start TUI in tmux session 'sonos'."""
    try:
        # First check if already running
        status_result = tui_status(args)
        status_data = json.loads(status_result)

        if status_data.get("running"):
            return f"Error: TUI already running on pane {status_data.get('pane_id')}"

        # Check if tmux session 'sonos' exists
        session_check = subprocess.run(
            ["tmux", "has-session", "-t", "sonos"],
            capture_output=True,
            timeout=2
        )
        session_exists = session_check.returncode == 0

        # Create session if needed
        if not session_exists:
            subprocess.run(
                ["tmux", "new-session", "-d", "-s", "sonos"],
                check=True,
                timeout=5
            )

        # Get the pane ID for the sonos session
        pane_result = subprocess.run(
            ["tmux", "list-panes", "-t", "sonos", "-F", "#{pane_id}"],
            capture_output=True,
            text=True,
            check=True,
            timeout=2
        )
        pane_id = pane_result.stdout.strip().split('\n')[0]

        # Launch TUI in the tmux pane
        tui_script = Path(__file__).parent / "sonos_interactive_tui.py"
        python_exe = sys.executable

        subprocess.run(
            ["tmux", "send-keys", "-t", pane_id, f"{python_exe} {tui_script}", "Enter"],
            check=True,
            timeout=2
        )

        # Wait briefly for TUI to start and write state file
        time.sleep(1)

        # Verify it started
        verify_result = tui_status(args)
        verify_data = json.loads(verify_result)

        if verify_data.get("running"):
            return f"TUI started successfully on pane {pane_id}"
        else:
            return f"Warning: TUI launch command sent to pane {pane_id}, but status check failed. Check manually."

    except subprocess.TimeoutExpired:
        return "Error: tmux command timed out"
    except FileNotFoundError:
        return "Error: tmux not found. Please install tmux."
    except subprocess.CalledProcessError as e:
        return f"Error: tmux command failed: {e}"
    except Exception as e:
        return handle_error(e, "tui_start")


@tool("tui_stop")
def tui_stop(args):
    """Stop running TUI gracefully."""
    try:
        # Check if TUI is running
        status_result = tui_status(args)
        status_data = json.loads(status_result)

        if not status_data.get("running"):
            return "TUI not running"

        pane_id = status_data.get("pane_id")
        if not pane_id or pane_id == "unknown":
            return "Error: Cannot determine TUI pane ID"

        # Send quit command to TUI
        subprocess.run(
            ["tmux", "send-keys", "-t", pane_id, "quit", "Enter"],
            check=True,
            timeout=2
        )

        # Wait for graceful shutdown (up to 3 seconds)
        for _ in range(6):
            time.sleep(0.5)
            verify_result = tui_status(args)
            verify_data = json.loads(verify_result)
            if not verify_data.get("running"):
                return "TUI stopped successfully"

        # If still running after 3 seconds, report issue
        return "Warning: TUI may still be running. Sent quit command but process did not stop within 3 seconds."

    except subprocess.TimeoutExpired:
        return "Error: tmux command timed out"
    except FileNotFoundError:
        return "Error: tmux not found. Please install tmux."
    except subprocess.CalledProcessError as e:
        return f"Error: tmux command failed: {e}"
    except Exception as e:
        return handle_error(e, "tui_stop")


@tool("tui_wait_for_prompt")
def tui_wait_for_prompt(args):
    """Wait for TUI to reach a specific prompt state.

    This tool efficiently polls the TUI state file instead of using fixed sleep times.
    Use this after sending commands to wait for TUI to be ready for next input.

    Args:
        expected_prompt: One of 'search', 'select', 'play'
        timeout: Optional timeout in seconds (default: 5.0)

    Returns:
        Success message with elapsed time when prompt reached, or timeout error

    Example workflow:
        1. send_keys "album: Harvest Moon"
        2. tui_wait_for_prompt "select"  # Wait until TUI shows selection prompt
        3. capture_pane to see results
        4. send_keys "1"
        5. tui_wait_for_prompt "play"    # Wait until TUI asks about playback
        6. send_keys "y"
        7. tui_wait_for_prompt "search"  # Wait until back to search prompt
    """
    if len(args) < 3:
        return "Error: expected_prompt required (one of: search, select, play)"

    expected_prompt = args[2]
    valid_prompts = {'search', 'select', 'play'}

    if expected_prompt not in valid_prompts:
        return f"Error: expected_prompt must be one of: {', '.join(sorted(valid_prompts))}"

    # Parse optional timeout (default 5 seconds)
    timeout = 5.0
    if len(args) >= 4:
        try:
            timeout = float(args[3])
            if timeout <= 0:
                return "Error: timeout must be positive"
        except ValueError:
            return "Error: timeout must be a number"

    state_file = Path.home() / ".sonos" / "tui_state.json"
    start_time = time.time()
    poll_interval = 0.1  # Poll every 100ms

    while time.time() - start_time < timeout:
        try:
            if state_file.exists():
                with open(state_file) as f:
                    state = json.load(f)

                current_prompt = state.get("current_prompt")

                # Check if we've reached the expected prompt
                if current_prompt == expected_prompt:
                    elapsed = time.time() - start_time
                    return f"TUI ready at '{expected_prompt}' prompt (waited {elapsed:.2f}s)"

            # Sleep before next poll
            time.sleep(poll_interval)

        except json.JSONDecodeError:
            # State file might be mid-write, retry
            time.sleep(poll_interval)
            continue
        except Exception as e:
            return f"Error checking TUI state: {e}"

    # Timeout reached - provide diagnostic info
    try:
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
            current = state.get("current_prompt", "unknown")
            return f"Timeout waiting for '{expected_prompt}' prompt (currently at: '{current}', waited {timeout:.1f}s)"
    except:
        pass

    return f"Timeout waiting for '{expected_prompt}' prompt (waited {timeout:.1f}s)"


def main():
    """Main dispatcher entry point."""
    if len(sys.argv) < 2:
        print("Usage: sonos_tool.py <tool_name> [args...]", file=sys.stderr)
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

    # Initialize speaker (except for tools that don't need speaker connection)
    no_speaker_tools = {"get_master_speaker", "tui_status", "tui_start", "tui_stop", "tui_wait_for_prompt"}
    if tool_name not in no_speaker_tools:
        initialize_speaker()

    # Execute tool
    try:
        result = TOOLS[tool_name](sys.argv)
        print(result)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
