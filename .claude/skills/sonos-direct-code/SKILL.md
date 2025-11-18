---
name: sonos-direct-code
description: "[DIRECT MODE - DEFAULT] Direct Python access to Sonos control via dispatcher tool. Use this skill for ALL Sonos requests when running in direct mode (default). Provides 21 discrete tools matching MCP mode functionality and 3 additional tools to manage tmux access to sonos_interactive_tui.py."
---

# Sonos Direct Code Access Skill

This skill provides guidance for using the Sonos dispatcher tool (`sonos_tool.py`) for Sonos speaker control. The dispatcher exposes 21 discrete tools that match the MCP server functionality plus 3 additional tools for managing the Interactive TUI (`sonos_interactive_tui.py`), all executing directly without protocol overhead for maximum token efficiency.

## Quick Start

### Two Approaches Available

**1. CLI Dispatcher Tools** (recommended for most operations):

**IMPORTANT: Use the Bash tool directly - DO NOT use tmux for CLI dispatcher commands!**

```bash
# Execute with Bash tool (NOT tmux)
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py <tool_name> [args...]
```

**2. Interactive TUI** (ONLY used to search for tracks or albums and place them on the queue and OPTIONALLY to play the track immediately):

**IMPORTANT: This is the ONLY use case for tmux tools (via tmux_tool.py dispatcher)!**

```bash
# Launch in tmux session (ONLY for interactive TUI)
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_interactive_tui.py
```

### CRITICAL: When to Use Each Approach

**Use CLI Dispatcher (with Bash tool - NO tmux):**
- ✅ Single operations (list_queue, clear_queue, play_from_queeu, volume, etc.)
- ✅ Do not use for searches because searches require multiple steps: 1) searching for a track or album; 2) placing the track or album on the queue(where it is appended to the end) and 3) optionally playing from the position of the added track or album on the queue.
- ❌ NEVER use tmux tools to run CLI dispatcher commands

**Use Interactive TUI (with tmux_tool.py for interaction):**
- ✅ for all search-related actions since they are always multi-step
- ❌ NOT for non-search operations (volume, current track, etc.)
- See tmux-tool skill for tmux interaction tools

### CLI Dispatcher Examples

**Execute these with the Bash tool directly (NOT tmux):**
```bash

# List the queue - use Bash tool
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py list_queue

# Set volume - use Bash tool
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py set_volume 50
```

**Key Features:**
- Speaker automatically initialized (no manual `set_master()` needed)
- All 21 tools available (same as MCP mode) but don't use the CLI search tools, use the tmux TUI for searches
- Standardized error handling
- Results printed to stdout for agent inspection

### TUI Lifecycle Management

**NEW: Three convenience tools for managing the Interactive TUI**

Before working with the Interactive TUI (`sonos_interactive_tui.py`), use these tools to manage its lifecycle:

**1. Check if TUI is running:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py tui_status
```

Returns JSON with:
- `running`: true/false
- `status`: "running", "stopped", "not_running", or "stale"
- `current_prompt`: "search", "select", or "play" (if running)
- `pid`: Process ID (if running)
- `pane_id`: tmux pane ID (if running)

**2. Start TUI in background:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py tui_start
```

- Automatically creates tmux session "sonos" if needed
- Launches TUI in the session
- Returns pane ID on success
- Returns error if TUI already running

**3. Stop TUI gracefully:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py tui_stop
```

- Sends quit command to TUI
- Waits up to 3 seconds for shutdown
- Returns success/failure status

**Recommended Workflow:**
1. Always call `tui_status` first to check if TUI is already running
2. If not running, call `tui_start` to launch it
3. Use tmux_tool.py for TUI interaction (capture/send keys)
4. When done, optionally call `tui_stop` to clean up

**Example:**
```bash
# Step 1: Check status
/home/slzatz/sonos_mcp/.venv/bin/python3 .../sonos_tool.py tui_status
# Returns: {"running": false, "status": "not_running", ...}

# Step 2: Start TUI
/home/slzatz/sonos_mcp/.venv/bin/python3 .../sonos_tool.py tui_start
# Returns: "TUI started successfully on pane %0"

# Step 3: Interact via tmux_tool.py (see tmux-tool skill)
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 40
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "search query"

# Step 4: Stop when done
/home/slzatz/sonos_mcp/.venv/bin/python3 .../sonos_tool.py tui_stop
```

## Interactive TUI Approach (Experimental)

**IMPORTANT: tmux tools (via tmux_tool.py) are ONLY for TUI interaction - NOT for CLI dispatcher commands!**

**When to use this:**
- ALL search operations (track or album searches)
- User explicitly requests interactive queue building workflow
- Multiple search-select-add cycles in succession

**When NOT to use this:**
- Any non-search operations (use CLI dispatcher with Bash tool)
- You want to run CLI dispatcher commands (NEVER use tmux for that!)

### Overview

The `sonos_interactive_tui.py` script (located in project root) provides a running interactive interface that allows you to:
1. Search for tracks or albums
2. See results and select the best match
3. Add to queue with the option of immediate playback
4. Loop back for more searches - all within a single running process

**Search Type Control:**
- **Track search (default):** Just enter your query (e.g., `Heart of Gold Neil Young`)
- **Album search:** Prefix query with `album:` (e.g., `album: Harvest Neil Young`)
  - **IMPORTANT:** Use `album:` with colon (preferred) or `album ` with space
  - Both formats work, but colon is preferred for clarity
  - Example: `album: Nebraska Bruce Springsteen` or `album Nebraska Bruce Springsteen`

The TUI automatically detects the prefix and uses the appropriate search and add functions.

**This leverages tmux's ability to:**
- Launch and keep a TUI running
- Capture the current display state
- Send keystrokes to the running application
- Repeat the interaction cycle

### TUI Workflow Pattern

**IMPORTANT: Session Convention**
- Always use session name: `"sonos"`
- Create the session if it doesn't exist (use tui_start or tmux_tool.py)
- Use the first available pane from the session

**Step 0: Ensure tmux session exists and get pane ID**

Use tmux_tool.py (see tmux-tool skill for details) or tui_start from sonos_tool.py:

```bash
# Option 1: Use tui_start (recommended - handles everything)
python3 .claude/skills/sonos-direct-code/sonos_tool.py tui_start
# Returns: "TUI started successfully on pane %0"

# Option 2: Manual session setup with tmux_tool.py
python3 .claude/skills/tmux-tool/tmux_tool.py session_ready sonos
# Returns: "Session 'sonos' created. Pane ready: %0"
```

**Step 1: Launch TUI (if using manual approach)**
```bash
# If not using tui_start, launch TUI manually
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 \
  "cd /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code && /home/slzatz/sonos_mcp/.venv/bin/python3 sonos_interactive_tui.py"
```

**Step 2: Capture initial state**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 40
```

You'll see:
```
================================================================================
Sonos Interactive Track and Album Search
================================================================================
Commands: Type search query, track/album number, or 'quit' to exit

Initializing Sonos speaker...
Connected to: Office2

Search:
```

**Step 3: Send search query**

For track search (default):
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "Heart of Gold Neil Young"
```

For album search (use `album:` prefix):
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "album: Harvest Neil Young"
```

**Step 4: Capture search results**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 60
```

You'll see numbered results:
```
Found 50 results:
--------------------------------------------------------------------------------
1. Heart of Gold - Neil Young - Harvest
2. Heart of Gold - Old Man With A Heart... - Neil Young We Miss Streaming You
3. Heart of Gold (Cover) - ...
...
--------------------------------------------------------------------------------

Select track (1-50) or 'q' to search again:
```

**Step 5: Analyze results and send selection**

Examine the results and pick the best match. Send the item number (track or album):

```bash
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "1"
```

**Step 6: Capture queue confirmation**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 20
```

You'll see:
```
Adding track 1 to queue...
Track added at position 12.
Play now? (y/n):
```

**Step 7: Choose whether to play immediately**

```bash
# To play now:
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "y"

# Or just queue it:
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "n"
```

**Step 8: Loop continues**

After your choice, the TUI returns to the search prompt:
```
Now playing track 12!

================================================================================

Search:
```

You can now search for another track, or quit:
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "quit"
```

### TUI State Management

The TUI maintains state across operations:
- Search results are cached (saved to `~/.sonos/search_results/track_search.json`)
- Queue position tracking (automatically counts queue length)
- Continuous loop until you explicitly quit

### TUI Commands

While in the TUI, you can send:
- **Search query** (any text at "Search:" prompt)
  - For track search: `Heart of Gold Neil Young` (default)
  - For album search: `album: Harvest Neil Young` (preferred) or `album Harvest Neil Young`
  - **TIP:** Use colon for clarity, but space also works
- **Track/Album number** (1-N at "Select track:" prompt)
- **"q"** or **"quit"** (to exit TUI or return to search)
- **"y"** or **"n"** (at "Play now?" prompt)

### TUI vs CLI Dispatcher Comparison

| Feature | Interactive TUI | CLI Dispatcher |
|---------|----------------|----------------|
| **Process lifecycle** | Runs continuously | Tool invoked per operation |
| **State** | Maintains state | Stateless (reads from files) |
| **Search workflow** | Integrated (search → select → play) | No search capability |
| **Used for** | Searches, queue building | ALL other tasks |
| **Uses tmux** | Yes | No |
| **Control flow** | Sequential prompts | Explicit tool selection |

### TUI Implementation Details

**File Location:** `/home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_interactive_tui.py`

**tmux Requirements:**
- **Session name convention**: `"sonos"` (always use this name)
- **Automatic creation**: Use `tui_start` or `tmux_tool.py session_ready` to setup session
- **Session check**: Use `tmux_tool.py find_session` to verify session exists
- **Pane ID**: Get from `tmux_tool.py get_pane` (typically `"%0"` for first pane)

**Dependencies:**
- Uses `sonos_actions` library for all Sonos operations
- Saves search results to same JSON files as CLI tools
- Compatible with existing search result caching
- Requires tmux tools (via tmux_tool.py dispatcher from tmux-tool skill)

**Features:**
- Clear prompts designed for tmux capture
- Error handling with user-friendly messages
- Automatic speaker initialization on startup
- Queue position tracking for accurate playback

### Example: Building a Queue with TUI

Here's a complete example of using the TUI to build a queue of multiple tracks:

```python
# Step 0: Ensure "sonos" tmux session exists and launch TUI
# Use tui_start (recommended - handles everything):
python3 .claude/skills/sonos-direct-code/sonos_tool.py tui_start
# Returns: "TUI started successfully on pane %0"

# OR manual approach with tmux_tool.py:
python3 .claude/skills/tmux-tool/tmux_tool.py session_ready sonos  # Get pane ID
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "cd /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code && /home/slzatz/sonos_mcp/.venv/bin/python3 sonos_interactive_tui.py"

# Search for first track
execute_command(paneId="%0", command="Neil Young Heart of Gold", rawMode=true)
capture_pane(paneId="%0")  # See results
execute_command(paneId="%0", command="1", rawMode=true)  # Select track 1
execute_command(paneId="%0", command="n", rawMode=true)  # Queue, don't play yet

# Search for an album (note the "album:" prefix)
execute_command(paneId="%0", command="album: Harvest Neil Young", rawMode=true)
capture_pane(paneId="%0")  # See album results
execute_command(paneId="%0", command="1", rawMode=true)  # Select album 1
execute_command(paneId="%0", command="n", rawMode=true)  # Queue all tracks, don't play yet

# Search for third track
execute_command(paneId="%0", command="Leonard Cohen Suzanne", rawMode=true)
capture_pane(paneId="%0")  # See results
execute_command(paneId="%0", command="1", rawMode=true)  # Select track 1
execute_command(paneId="%0", command="y", rawMode=true)  # Queue and start playing!

# Exit TUI
execute_command(paneId="%0", command="quit", rawMode=true)
```

This builds a queue with tracks and a full album, then starts playback - all within one continuous TUI session. The example demonstrates mixing track searches with album searches using the `album:` prefix.

## When to Use Direct Mode

**Use this approach when:**
- Running in direct mode (default for `sdk_agent.py`)
- Want maximum token efficiency (~15% savings vs MCP mode)
- Need discrete, predictable tool behavior
- Building conversational workflows

**Use MCP mode instead when:**
- Running in mcp mode
- Need portability across AI platforms
- Working in Claude Desktop or other MCP clients
- Want standard protocol compliance
- Multi-client scenarios

## Available Tools (22 Total)

The dispatcher provides these tools. Most tools automatically initialize the speaker connection (TUI lifecycle tools do not require speaker connection).

**IMPORTANT:** There are NO CLI search tools - ALL searches must use the Interactive TUI!

### Speaker Management (2 tools)

#### `get_master_speaker`
Get the currently configured master speaker name.

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py get_master_speaker
```

#### `set_master_speaker <speaker_name>`
Change the master speaker to a different Sonos device.

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py set_master_speaker "Bedroom"
```

### Music Search (0 CLI tools)

**CRITICAL: There are NO CLI search tools available!**

- ❌ `search_for_track` - NOT AVAILABLE as CLI tool
- ❌ `search_for_album` - NOT AVAILABLE as CLI tool
- ✅ **Use the Interactive TUI for ALL search operations** (tracks and albums)

All music searches (both tracks and albums) MUST use the Interactive TUI workflow described above. The CLI dispatcher does NOT provide search tools.

### Queue Management (6 tools)

#### `list_queue`
Display the current Sonos queue showing all queued tracks.

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py list_queue
```

#### `add_track_to_queue <position>`
Add track from search results to queue (1-indexed position).

**IMPORTANT: This tool ONLY adds to queue - it does NOT start playback!**
You must call `play_from_queue` separately to play the track.

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py add_track_to_queue 1
```

**No flags/options:** This tool takes only the position number - no `--play` or other flags exist.

#### `add_album_to_queue <position>`
Add album from search results to queue (1-indexed position).

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py add_album_to_queue 1
```

#### `clear_queue`
Clear all tracks from the current queue.

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py clear_queue
```

#### `remove_from_queue <position>`
Remove track from queue by position (1-indexed).

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py remove_from_queue 3
```

#### `play_from_queue <position>`
Play track from queue by position (1-indexed).

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py play_from_queue 1
```

### Playback Control (3 tools)

#### `current_track`
Get information about what's currently playing.

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py current_track
```

#### `play_pause`
Toggle play/pause of the current track.

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py play_pause
```

#### `next_track`
Skip to the next track in the queue.

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py next_track
```

### Volume Control (3 tools)

#### `turn_volume <direction>`
Adjust volume up or down by 10 (`louder` or `quieter`).

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py turn_volume louder
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py turn_volume quieter
```

#### `set_volume <level>`
Set absolute volume level (0-100).

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py set_volume 50
```

#### `mute <true|false>`
Mute or unmute all speakers in the group.

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py mute true
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py mute false
```

### Playlist Management (5 tools)

#### `list_playlists`
List all available local playlists.

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py list_playlists
```

#### `add_to_playlist_from_queue <playlist> <position>`
Add track from queue to a playlist (position is 1-indexed).

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py add_to_playlist_from_queue favorites 3
```

#### `add_to_playlist_from_search <playlist> <position>`
Add track from search results to a playlist (position is 1-indexed).

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py add_to_playlist_from_search favorites 1
```

#### `add_playlist_to_queue <playlist> [shuffle]`
Load playlist to queue. Optional `shuffle` parameter (true/false).

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py add_playlist_to_queue favorites
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py add_playlist_to_queue favorites true
```

#### `list_playlist_tracks <playlist>`
Display all tracks in a saved playlist.

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py list_playlist_tracks favorites
```

#### `remove_track_from_playlist <playlist> <position>`
Remove track from playlist by position (1-indexed).

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py remove_track_from_playlist favorites 5
```

#### `list_native_sonos_playlists`
List all native Sonos playlists stored on the Sonos system.

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py list_native_sonos_playlists
```

#### `create_native_sonos_playlist_from_local <local_playlist> [native_name]`
Create native Sonos playlist from local playlist file.

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py create_native_sonos_playlist_from_local favorites "My Favorites"
```

### TUI Lifecycle Management (3 tools)

These tools manage the Interactive TUI (`sonos_interactive_tui.py`) process lifecycle. Unlike other tools, these do NOT require speaker initialization.

#### `tui_status`
Check if the Interactive TUI is running and get its current state.

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py tui_status
```

**Returns:** JSON with status information:
```json
{
  "running": true,
  "status": "running",
  "current_prompt": "search",
  "pid": 12345,
  "pane_id": "%0",
  "last_updated": "2025-01-16T10:30:00"
}
```

**Possible status values:**
- `"not_running"`: TUI not running (no state file found)
- `"stopped"`: TUI was stopped gracefully
- `"running"`: TUI is currently active
- `"stale"`: State file exists but process/pane not found

#### `tui_start`
Start the Interactive TUI in tmux session "sonos".

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py tui_start
```

**Behavior:**
- Creates tmux session "sonos" if it doesn't exist
- Launches TUI in that session's first pane
- Waits 1 second for initialization
- Verifies TUI started successfully
- Returns pane ID (e.g., "%0") on success
- Returns error if TUI already running

**Example output:**
```
TUI started successfully on pane %0
```

**Error if already running:**
```
Error: TUI already running on pane %0
```

#### `tui_stop`
Stop the running Interactive TUI gracefully.

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py tui_stop
```

**Behavior:**
- Checks if TUI is running via `tui_status`
- Sends "quit" command to TUI via tmux
- Waits up to 3 seconds for graceful shutdown
- Verifies process stopped

**Example output:**
```
TUI stopped successfully
```

**If not running:**
```
TUI not running
```

## Common Workflows

These workflows demonstrate how to combine multiple tools for common tasks. Remember: The dispatcher path is long, so store it in a variable in your workflow for readability (if combining multiple calls).

### Search and Play Music (Tracks or Albums)

**IMPORTANT: uses tmux and sonos_interactive_tui.py

Session Convention**
- Always use session name: `"sonos"`
- Create the session if it doesn't exist
- Use the first available pane from the session

**Step 0: Ensure tmux session exists**

Before launching the TUI, you MUST ensure a tmux session named "sonos" exists:

```python
# Check if "sonos" session exists
python3 .claude/skills/tmux-tool/tmux_tool.py find_session sonos

# If it doesn't exist (returns error/not found), create it:
python3 .claude/skills/tmux-tool/tmux_tool.py create_session sonos

# Get the session ID (usually "$0")
# List windows in the session
# Use get_pane instead of separate window/pane listing

# Get panes from the first window (usually "@0")
python3 .claude/skills/tmux-tool/tmux_tool.py get_pane sonos

# This gives you a pane ID (e.g., "%0") to use for the TUI
```

**Step 1: Launch TUI in tmux pane**
```python
# Launch the TUI in the pane you identified in Step 0
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0
  paneId="%0",  # Use the pane ID from Step 0
  command="cd /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code && /home/slzatz/sonos_mcp/.venv/bin/python3 sonos_interactive_tui.py",
  rawMode=true
)
```

**Step 2: Capture initial state**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 40
```

You'll see:
```
================================================================================
Sonos Interactive Track and Album Search
================================================================================
Commands: Type search query, track/album number, or 'quit' to exit

Initializing Sonos speaker...
Connected to: Office2

Search:
```

**Step 3: Send search query**

For track search (default):
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "Heart of Gold Neil Young"
```

For album search (use `album:` prefix):
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "album: Harvest Neil Young"
```

**Step 4: Capture search results**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 60
```

You'll see numbered results:
```
Found 50 results:
--------------------------------------------------------------------------------
1. Heart of Gold - Neil Young - Harvest
2. Heart of Gold - Old Man With A Heart... - Neil Young We Miss Streaming You
3. Heart of Gold (Cover) - ...
...
--------------------------------------------------------------------------------

Select the track or album (1-50) that best matches the request from the user or 'q' to search again:
```

**Step 5: Analyze results and send selection**

Examine the results and pick the best match. Send the item number (track or album):

```bash
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0
  paneId="%0",
  command="3",
  rawMode=true
)
```

**Step 6: Capture queue confirmation**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 20
```

You'll see:
```
Adding track 3 to queue...
Track added at position 12.
Play now? (y/n):
```

**Step 7: Choose whether to play immediately**

```bash
# To play now:
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "y"

# Or just queue it:
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "n"
```

**Step 8: Loop continues**

After your choice, the TUI returns to the search prompt:
```
Now playing track 12!

================================================================================

Search:
```

You can now search for another track, or quit:
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "quit"
```

### Load and Play a Playlist

```bash
# Clear existing queue
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py clear_queue

# Add playlist (shuffled)
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py add_playlist_to_queue favorites true

# Play first track
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py play_from_queue 1
```

### Build a Custom Playlist from Searches

```bash
# Search for first artist
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0paneId='%0', command='Joan Baez', rawMode=True)
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 50
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0paneId='%0', command='1', rawMode=True)
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 20
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0paneId='%0', command='n', rawMode=True)
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 20

# Add track to playlist (position 3)
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py add_to_playlist_from_queue my_mix 3

# Search for second artist
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0paneId='%0', command='Bob Dylan', rawMode=True)
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 50
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0paneId='%0', command='1', rawMode=True)
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 20
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0paneId='%0', command='n', rawMode=True)
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 20

# Add track to playlist (position 4)
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py add_to_playlist_from_queue my_mix 4
# View the playlist
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py list_playlist_tracks my_mix
```

### Check What's Playing and Control Playback

```bash
# Get current track
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py current_track

# Pause
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py play_pause

# Adjust volume
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py turn_volume louder

# Skip to next
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py next_track
```

### Create Native Sonos Playlist from Local

```bash
# List local playlists
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py list_playlists

# Convert to native Sonos playlist
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py create_native_sonos_playlist_from_local favorites "My Favorite Songs"

# Verify it was created
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py list_native_sonos_playlists
```

## Important Notes

1. **Tool Path:** The dispatcher tool is located at `/home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py` and must be called with the project's venv Python: `/home/slzatz/sonos_mcp/.venv/bin/python3`

2. **Automatic Initialization:** The dispatcher automatically initializes the speaker connection - you don't need to call `set_master()` manually.

3. **Search Result Caching:** Search functions save results to `~/.sonos/search_results/` JSON files. Multiple adds from the same search will read from the cached file.

4. **Queue Positions:**
   - All tools use **1-indexed positions** (position 1 = first item, position N = last item)
   - When you add a track, it goes to the END of the queue
   - Always use `list_queue` after adding to find the new position (count total tracks)
   - **Position must be positive** (1 to queue length) - negative numbers are NOT allowed

5. **Local vs Native Playlists:**
   - **Local playlists:** Stored in `~/.sonos/playlists/` as JSON files, managed by these tools
   - **Native Sonos playlists:** Stored on Sonos system, accessible from Sonos app and other controllers
   - Use `create_native_sonos_playlist_from_local` to convert between them

6. **Error Handling:** All tools provide user-friendly error messages. Check tool output for errors.

7. **Music Service:** Searches use the music service configured in `sonos/config.py` (default: "Amazon Music").

## File Locations

### Search Results Cache
- **Track search:** `~/.sonos/search_results/track_search.json`
- **Album search:** `~/.sonos/search_results/album_search.json`

Format:
```json
[
  {
    "title": "Heart of Gold",
    "artist": "Neil Young",
    "album": "Harvest",
    "item_id": "catalog/tracks/B001...",
    "uri": "x-sonos-http:..."
  }
]
```

### Local Playlists
- **Location:** `~/.sonos/playlists/`
- **Format:** JSON files, one per playlist

Format:
```json
[
  {
    "title": "Heart of Gold",
    "artist": "Neil Young",
    "album": "Harvest",
    "item_id": "catalog/tracks/...",
    "uri": "soco://0fffffff..."
  }
]
```

## Configuration

### `sonos/config.py` (User-created)
```python
master_speaker = "Office2"           # Default speaker name
music_service = "Amazon Music"       # Music service for searches
api_url = "https://genius.com/api"  # For lyrics (optional)
```

## Troubleshooting

### Speaker Connection Issues
If tools fail with connection errors:
1. Verify speaker is powered on and on network
2. Check `sonos/config.py` has correct speaker name (case-sensitive)
3. Use `get_master_speaker` to verify connection
4. Use `set_master_speaker` to switch speakers if needed

### Search Returns No Results
- Try different query formats (artist + title, title only, etc.)
- Check music service is correctly configured
- Verify track/album is available in your music service

### Queue Position Confusion
- Remember: Positions are 1-indexed (1 = first track)
- After adding tracks, use `list_queue` to see actual positions
- Tracks are added to the END of the queue, not the beginning

## When to Extend the Dispatcher

If you need new functionality:
1. Add function to `sonos/sonos_actions.py`
2. Add tool wrapper to `sonos_tool.py` (see existing tools as examples)
3. Update this skill documentation with new tool
4. Test with dispatcher before using in agent workflows

Alternatively, for very complex or experimental operations, you can still write inline Python code that imports `sonos_actions` directly, but this should be rare - the dispatcher tools should cover most use cases.
