---
name: tmux-tool
description: tmux session management and TUI interaction tools for direct mode. Use when you need to manage tmux sessions, capture pane output, or send keystrokes to interactive TUI applications.
---

# tmux Tool Dispatcher

CLI dispatcher providing tmux session management and TUI interaction tools for direct mode execution.

## Overview

This tool provides 6 discrete CLI tools for tmux operations, optimized for TUI (Terminal User Interface) interaction workflows:

- **Session Management**: find_session, create_session, get_pane
- **TUI Interaction**: capture_pane, send_keys
- **Convenience**: session_ready (all-in-one setup)

**Token Efficiency**: ~200-500 tokens vs ~2,000 tokens for tmux MCP server

**Architecture**: Follows the sonos_tool.py dispatcher pattern for consistency

## Available Tools

### Session Management Tools

#### find_session
Check if a tmux session exists by name.

**Usage:**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py find_session <session_name>
```

**Returns:**
- Session info if found (ID, name, window count)
- "Session not found" if doesn't exist

**Example:**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py find_session sonos
# Output: Session found: sonos (ID: $0, Windows: 1)
```

---

#### create_session
Create a new detached tmux session.

**Usage:**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py create_session <session_name>
```

**Returns:**
- Success confirmation
- "already exists" if session exists

**Example:**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py create_session sonos
# Output: Session 'sonos' created successfully
```

---

#### get_pane
Get pane ID for session (auto-creates session if doesn't exist).

**Usage:**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py get_pane <session_name>
```

**Returns:**
- Pane ID (e.g., "%0") ready for capture/send operations
- Creates session automatically if missing

**Example:**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py get_pane sonos
# Output: %0
```

---

### TUI Interaction Tools

#### capture_pane
Capture content from a tmux pane.

**Usage:**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane <pane_id> [lines]
```

**Parameters:**
- `pane_id` (required): Pane ID like "%0"
- `lines` (optional): Number of lines to capture (default: 40)

**Returns:**
- Pane content as text
- "No content captured" if empty

**Example:**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 40
# Output: <current TUI display content>
```

**Use Cases:**
- Read TUI application state
- Check what prompt/menu is displayed
- Verify command execution results
- Analyze search results

---

#### send_keys
Send keystrokes to a tmux pane.

**Usage:**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys <pane_id> <text> [enter]
```

**Parameters:**
- `pane_id` (required): Pane ID like "%0" - **MUST be the pane ID, NOT session name!**
- `text` (required): Text to send (single quotes are auto-escaped)
- `enter` (optional): Press Enter after text (default: "true", set "false" to skip)

**CRITICAL - Common Mistake:**
- ✅ CORRECT: `send_keys %0 "search query"`
- ❌ WRONG: `send_keys sonos 0 "search query"` (splits pane ID incorrectly!)
- ❌ WRONG: `send_keys sonos "search query"` (uses session name instead of pane ID!)

Always use the pane ID returned from `get_pane` or `session_ready` (e.g., "%0"), not the session name!

**Returns:**
- Success confirmation

**Example:**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "search Heart of Gold Neil Young"
# Output: Keys sent to pane %0

python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "1" false
# Output: Keys sent to pane %0 (no Enter pressed)
```

**Auto-escaping:**
- Single quotes in text are automatically escaped
- Example: "don't" → "don'\\''t" (handled internally)

---

### Convenience Tools

#### session_ready
Ensure session exists and return pane ID (all-in-one).

**Usage:**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py session_ready <session_name>
```

**Returns:**
- Pane ID with status message
- Creates session if needed
- Combines find_session + create_session + get_pane

**Example:**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py session_ready sonos
# Output: Session 'sonos' existing. Pane ready: %0
# or
# Output: Session 'sonos' created. Pane ready: %0
```

**Use Case:**
- Quick setup before TUI interaction
- Reduces tool calls from 3 to 1

---

## Common Workflows

### TUI Interaction Pattern

**1. Setup session and get pane:**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py session_ready sonos
# Output: Session 'sonos' created. Pane ready: %0
```

**2. Capture current TUI state:**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 40
# Read what's on screen
```

**3. Send input to TUI:**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "search query"
# TUI receives "search query" + Enter
```

**4. Capture updated state:**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 40
# See TUI response
```

**5. Repeat steps 3-4 for continued interaction**

---

### Sonos TUI Workflow (with sonos_interactive_tui.py)

**Prerequisites:**
- TUI started with tui_start (from sonos_tool.py)
- Session named "sonos" exists
- Pane ID available (usually %0)

**Search Type Control:**
- **Track search (default):** Send query without prefix (e.g., `Heart of Gold Neil Young`)
- **Album search:** Send query with `album:` prefix (e.g., `album: Harvest Neil Young`)
  - **IMPORTANT:** Prefer `album:` with colon, but `album ` with space also works
  - Examples: `album: Nebraska` (preferred) or `album Nebraska` (also works)

**Typical interaction cycle for track search:**

```bash
# 1. Get pane ID (CRITICAL: Save this for all subsequent commands!)
PANE_ID=$(python3 .claude/skills/tmux-tool/tmux_tool.py get_pane sonos)
# Returns: %0

# 2. Check TUI status (optional)
python3 .claude/skills/sonos-direct-code/sonos_tool.py tui_status
# Returns: running, pane_id: %0, current_prompt: search

# 3. Capture TUI display (use PANE_ID, NOT "sonos"!)
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 40
# See search prompt

# 4. Send search query (track search - default)
# CRITICAL: Use %0 (pane ID), NOT "sonos 0" or "sonos"!
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "Heart of Gold Neil Young"

# 4. Capture search results
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 60
# See numbered track list

# 5. Select track
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "1"

# 6. Confirm add/play
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "y"

# 7. Back to search prompt (repeat as needed)
```

**Typical interaction cycle for album search:**

```bash
# 1-2. Same as above (check status, capture display)

# 3. Send album search query (note the "album:" prefix)
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "album: Harvest Neil Young"

# 4. Capture album search results
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 60
# See numbered album list

# 5. Select album
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "1"
# Adds all album tracks to queue

# 6. Confirm add/play
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "y"

# 7. Back to search prompt (can mix track/album searches)
```

---

## Integration with sonos_tool.py

The TUI lifecycle tools in sonos_tool.py manage the interactive TUI process:

**tui_status** - Check if TUI is running
**tui_start** - Launch TUI in tmux session
**tui_stop** - Gracefully stop TUI

**Combined workflow:**
1. Use **sonos_tool.py tui_start** to launch TUI
2. Use **tmux_tool.py session_ready** to get pane ID
3. Use **tmux_tool.py capture_pane/send_keys** for interaction
4. Use **sonos_tool.py tui_stop** to gracefully exit

---

## Best Practices

### Pane ID Management
- Always use the pane ID returned by get_pane or session_ready
- Pane IDs are stable within a session (%0, %1, etc.)
- Re-verify pane ID if session was killed/recreated

### Error Handling
- Check tool output for "Error:" prefix
- Common errors:
  - "Session not found" → Use create_session or session_ready
  - "No panes found" → Session may be corrupted, recreate it
  - "tmux command failed" → tmux may not be installed/running

### Text Escaping
- send_keys auto-escapes single quotes
- No need to manually escape text
- Special characters are handled safely

### Capture Line Count
- Default 40 lines is good for most TUIs
- Increase for long menus (e.g., 100 lines)
- Decrease for quick status checks (e.g., 10 lines)

---

## Troubleshooting

### Session Not Found
```bash
# Check if session exists
python3 .claude/skills/tmux-tool/tmux_tool.py find_session sonos

# Create if missing
python3 .claude/skills/tmux-tool/tmux_tool.py create_session sonos

# Or use session_ready (auto-creates)
python3 .claude/skills/tmux-tool/tmux_tool.py session_ready sonos
```

### Pane Not Responding
```bash
# Verify pane exists
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0

# If error, get fresh pane ID
python3 .claude/skills/tmux-tool/tmux_tool.py get_pane sonos
```

### TUI State Unclear
```bash
# Capture more lines to see full context
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 100
```

---

## Technical Details

**Implementation:**
- Uses subprocess to call tmux commands
- Adapted from tmux-mcp server (https://github.com/nickgnd/tmux-mcp)
- Follows sonos_tool.py dispatcher pattern

**Dependencies:**
- tmux (must be installed and in PATH)
- Python 3.10+ (subprocess module)

**Quote Escaping:**
- Single quotes in text: `'` → `'\''`
- Pane IDs always quoted: `-t '{pane_id}'`
- Based on tmux-mcp tmux.ts:284 pattern

**Command Timeout:**
- All tmux commands timeout after 5 seconds
- Prevents hanging on invalid operations

---

## Examples

### Launch TUI and interact (full workflow)
```bash
# 1. Start TUI process
python3 .claude/skills/sonos-direct-code/sonos_tool.py tui_start
# Output: TUI started successfully on pane %0

# 2. Verify session ready
python3 .claude/skills/tmux-tool/tmux_tool.py session_ready sonos
# Output: Session 'sonos' existing. Pane ready: %0

# 3. Capture to see current state
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0
# Output: Enter search query (or 'quit' to exit):

# 4. Send search query
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "neil young"
# Output: Keys sent to pane %0

# 5. Capture results
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 40
# Output: <numbered search results>

# 6. Select and add track
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "2"
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "y"

# 7. Stop TUI when done
python3 .claude/skills/sonos-direct-code/sonos_tool.py tui_stop
# Output: TUI stopped successfully
```

---

## Design Philosophy

**Token Efficiency:**
- Minimal overhead (~200-500 tokens for skill metadata)
- No MCP protocol overhead (~2,000 tokens saved)

**Architectural Consistency:**
- Follows sonos_tool.py dispatcher pattern
- Same decorator registration approach
- Consistent error handling

**TUI-Optimized:**
- Tools designed for interactive TUI workflows
- Capture-send-repeat pattern
- Session management built-in

**Full Control:**
- All code in repository
- Easy to modify and extend
- No external MCP server dependency
