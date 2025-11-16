---
name: sonos-direct-code
description: "[DIRECT MODE - DEFAULT] Direct Python access to Sonos control via dispatcher tool. Use this skill for ALL Sonos requests when running in direct mode (default). Provides 21 discrete tools matching MCP mode functionality."
---

# Sonos Direct Code Access Skill

This skill provides guidance for using the Sonos dispatcher tool (`sonos_tool.py`) for Sonos speaker control. The dispatcher exposes 21 discrete tools that match the MCP server functionality but execute directly without protocol overhead for maximum token efficiency.

## Quick Start

### Two Approaches Available

**1. CLI Dispatcher Tools** (recommended for most operations):

**IMPORTANT: Use the Bash tool directly - DO NOT use tmux for CLI dispatcher commands!**

```bash
# Execute with Bash tool (NOT tmux)
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py <tool_name> [args...]
```

**2. Interactive TUI** (ONLY when building queues with multiple searches):

**IMPORTANT: This is the ONLY use case for tmux MCP tools!**

```bash
# Launch in tmux session (ONLY for interactive TUI)
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/sonos_interactive_tui.py
```

### CRITICAL: When to Use Each Approach

**Use CLI Dispatcher (with Bash tool - NO tmux):**
- ✅ Single operations (list_queue, clear_queue, play_from_queeu, volume, etc.)
- ✅ Do not use for searches because searches require multiple steps: 1) searching for a track or album; 2) placing the track or album on the queue(where it is appended to the end) and 3) optionally playing from the position of the added track or album on the queue.
- ❌ NEVER use `mcp__tmux__execute-command` to run CLI dispatcher tools

**Use Interactive TUI (with tmux MCP tools):**
- ✅ for all search-related actions since they are always multi-step
- ❌ NOT for non-search operations (volume, current track, etc.)

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

## Interactive TUI Approach (Experimental)

**IMPORTANT: tmux MCP tools are ONLY for this Interactive TUI - NOT for CLI dispatcher commands!**

**When to use this:**
- ALL search operations (track or album searches)
- User explicitly requests interactive queue building workflow
- Multiple search-select-add cycles in succession

**When NOT to use this:**
- Any non-search operations (use CLI dispatcher with Bash tool)
- You want to run CLI dispatcher commands (NEVER use tmux for that!)

### Overview

The `sonos_interactive_tui.py` script (located in project root) provides a running interactive interface that allows you to:
1. Search for tracks
2. See results and select the best match
3. Add to queue with the option of immediate playback
4. Loop back for more searches - all within a single running process

**This leverages tmux's ability to:**
- Launch and keep a TUI running
- Capture the current display state
- Send keystrokes to the running application
- Repeat the interaction cycle

### TUI Workflow Pattern

**IMPORTANT: Session Convention**
- Always use session name: `"sonos"`
- Create the session if it doesn't exist
- Use the first available pane from the session

**Step 0: Ensure tmux session exists**

Before launching the TUI, you MUST ensure a tmux session named "sonos" exists:

```python
# Check if "sonos" session exists
mcp__tmux__find-session(name="sonos")

# If it doesn't exist (returns error/not found), create it:
mcp__tmux__create-session(name="sonos")

# Get the session ID (usually "$0")
# List windows in the session
mcp__tmux__list-windows(sessionId="$0")

# Get panes from the first window (usually "@0")
mcp__tmux__list-panes(windowId="@0")

# This gives you a pane ID (e.g., "%0") to use for the TUI
```

**Step 1: Launch TUI in tmux pane**
```python
# Launch the TUI in the pane you identified in Step 0
mcp__tmux__execute-command(
  paneId="%0",  # Use the pane ID from Step 0
  command="cd /home/slzatz/sonos_mcp && .venv/bin/python3 sonos_interactive_tui.py",
  rawMode=true
)
```

**Step 2: Capture initial state**
```bash
mcp__tmux__capture-pane(paneId="%0", lines=40)
```

You'll see:
```
================================================================================
Sonos Interactive Track Search
================================================================================
Commands: Type search query, track number, or 'quit' to exit

Initializing Sonos speaker...
Connected to: Office2

Search:
```

**Step 3: Send search query**
```bash
mcp__tmux__execute-command(
  paneId="%0",
  command="Heart of Gold Neil Young",
  rawMode=true
)
```

**Step 4: Capture search results**
```bash
mcp__tmux__capture-pane(paneId="%0", lines=60)
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

Examine the results and pick the best match. Send the track number:

```bash
mcp__tmux__execute-command(
  paneId="%0",
  command="1",
  rawMode=true
)
```

**Step 6: Capture queue confirmation**
```bash
mcp__tmux__capture-pane(paneId="%0", lines=20)
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
mcp__tmux__execute-command(paneId="%0", command="y", rawMode=true)

# Or just queue it:
mcp__tmux__execute-command(paneId="%0", command="n", rawMode=true)
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
mcp__tmux__execute-command(paneId="%0", command="quit", rawMode=true)
```

### TUI State Management

The TUI maintains state across operations:
- Search results are cached (saved to `~/.sonos/search_results/track_search.json`)
- Queue position tracking (automatically counts queue length)
- Continuous loop until you explicitly quit

### TUI Commands

While in the TUI, you can send:
- **Search query** (any text at "Search:" prompt)
- **Track number** (1-N at "Select track:" prompt)
- **"q"** or **"quit"** (to exit TUI)
- **"y"** or **"n"** (at "Play now?" prompt)

### TUI vs CLI Dispatcher Comparison

| Feature | Interactive TUI | CLI Dispatcher |
|---------|----------------|----------------|
| **Process lifecycle** | Runs continuously | Tool invoked per operation |
| **State** | Maintains state | Stateless (reads from files) |
| **Search workflow** | Integrated (search → select → play) | Manual steps (separate tool calls) |
| **Best for** | Multiple searches, queue building | Single operations, specific tasks |
| **Token efficiency** | High (fewer tool calls) | Moderate (each operation = tool call) |
| **Requires tmux** | Yes | No |
| **Control flow** | Sequential prompts | Explicit tool selection |

### TUI Implementation Details

**File Location:** `/home/slzatz/sonos_mcp/sonos_interactive_tui.py`

**tmux Requirements:**
- **Session name convention**: `"sonos"` (always use this name)
- **Automatic creation**: Create the session if it doesn't exist with `mcp__tmux__create-session`
- **Session check**: Always verify session exists with `mcp__tmux__find-session` before use
- **Pane ID**: Get from `mcp__tmux__list-panes` (typically `"%0"` for first pane)

**Dependencies:**
- Uses `sonos_actions` library for all Sonos operations
- Saves search results to same JSON files as CLI tools
- Compatible with existing search result caching
- Requires tmux MCP server tools (`mcp__tmux__*`)

**Features:**
- Clear prompts designed for tmux capture
- Error handling with user-friendly messages
- Automatic speaker initialization on startup
- Queue position tracking for accurate playback

### Example: Building a Queue with TUI

Here's a complete example of using the TUI to build a queue of multiple tracks:

```python
# Step 0: Ensure "sonos" tmux session exists
mcp__tmux__find-session(name="sonos")  # Check if exists
# If not found, create it:
mcp__tmux__create-session(name="sonos")
# Get pane ID from session
mcp__tmux__list-windows(sessionId="$0")
mcp__tmux__list-panes(windowId="@0")  # Get pane ID like "%0"

# Step 1: Launch TUI in the sonos session pane
mcp__tmux__execute-command(paneId="%0", command="cd /home/slzatz/sonos_mcp && .venv/bin/python3 sonos_interactive_tui.py", rawMode=true)

# Search for first artist
execute_command(paneId="%0", command="Neil Young Heart of Gold", rawMode=true)
capture_pane(paneId="%0")  # See results
execute_command(paneId="%0", command="1", rawMode=true)  # Select track 1
execute_command(paneId="%0", command="n", rawMode=true)  # Queue, don't play yet

# Search for second artist
execute_command(paneId="%0", command="Bob Dylan Tangled Up in Blue", rawMode=true)
capture_pane(paneId="%0")  # See results
execute_command(paneId="%0", command="2", rawMode=true)  # Select track 2
execute_command(paneId="%0", command="n", rawMode=true)  # Queue, don't play yet

# Search for third artist
execute_command(paneId="%0", command="Leonard Cohen Suzanne", rawMode=true)
capture_pane(paneId="%0")  # See results
execute_command(paneId="%0", command="1", rawMode=true)  # Select track 1
execute_command(paneId="%0", command="y", rawMode=true)  # Queue and start playing!

# Exit TUI
execute_command(paneId="%0", command="quit", rawMode=true)
```

This builds a 3-track queue and starts playback - all within one continuous TUI session.

## Critical Workflow Rules

### MANDATORY Two-Step Workflow for Search Operations

**YOU MUST ALWAYS use a two-step approach when searching for and adding music:**

**CRITICAL: "Two-Step" means TWO SEPARATE TOOL CALLS, not two tools in one command!**

**Why This Is Mandatory:**
- Search results are unpredictable and context-dependent
- The best match is **NOT always position 1**
- Artist name variations (Bill Callahan vs. Smog, for example)
- Multiple versions exist (remaster, live, cover, original, etc.)
- You MUST examine results before selecting which position to add

**The Two-Step Pattern (TWO SEPARATE TOOL CALLS):**

**Step 1: FIRST TOOL CALL - Search ONLY**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py search_for_track "Bill Callahan The Breeze"
```

**STOP HERE! Examine the output. DO NOT add anything yet.**

**Then:** Read the search results, identify which position is the best match, communicate your selection to the user.

**Step 2: SECOND TOOL CALL - Add ONLY**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py add_track_to_queue 3
```

**Key Point:** These are TWO SEPARATE Bash tool calls. After the first one completes, you see the results, analyze them, then make the second call.

**Example - Correct Workflow for "Play a Track":**

User asks: "Play Bill Callahan's version of The Breeze"

**Step 1: Search**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py search_for_track "Bill Callahan The Breeze"
```

**Step 2: Examine Results & Select**
Agent analyzes output: "Position 3 is specifically by Bill Callahan, that's the one!"

**Step 3: Add to Queue**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py add_track_to_queue 3
```

**IMPORTANT: `add_track_to_queue` ONLY adds the track - it does NOT start playing!**

**Step 4: List Queue to Find Position**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py list_queue
```

**Step 5: Play from That Position** (REQUIRED - adding doesn't auto-play!)
```bash
# If queue shows 5 tracks total, the newly added track is at position 5
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py play_from_queue 5
```

**NOTE:** There is NO `--play` flag or option on `add_track_to_queue`. You MUST call `play_from_queue` as a separate tool to start playback.

**CRITICAL: When you add a track to the queue, it goes to the END of the queue!**
- After adding a track, use `list_queue` to count how many tracks are in the queue
- The newly added track is at the LAST position (highest number)
- `play_from_queue` uses 1-based indexing (position 1 = first track, position N = last track)
- Position must be a positive integer from 1 to the queue length (no negative numbers!)

**Notice:** Multiple separate tool calls with analysis happening between them.

**NEVER Do This (Anti-Pattern):**
```bash
# ❌ WRONG - DO NOT DO THIS - trying to chain operations with && or ;
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py search_for_track "The Breeze" && /home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py add_track_to_queue 1
```

**Why the anti-pattern is wrong:**
- You haven't examined what position 1 actually is
- Position 1 might be a cover, live version, or wrong artist
- You're guessing instead of selecting based on actual results
- This defeats the purpose of having search results

**This applies to:**
- `search_for_track()` → `add_track_to_queue()`
- `search_for_album()` → `add_album_to_queue()`
- Any workflow where you search first then add

**Exception:**
The two-step pattern is not required for operations that don't involve searching:
- `list_queue()` - just displays queue
- `current_track_info()` - just shows current track
- `list_playlists()` - just lists playlists
- `add_playlist_to_queue()` - you already know the playlist name

## When to Use Direct Mode

**Use this approach when:**
- Running in direct mode (default for `sdk_agent.py`)
- Want maximum token efficiency (~15% savings vs MCP mode)
- Need discrete, predictable tool behavior
- Building conversational workflows

**Use MCP mode instead when:**
- Need portability across AI platforms
- Working in Claude Desktop or other MCP clients
- Want standard protocol compliance
- Multi-client scenarios

## Available Tools (21 Total)

The dispatcher provides these tools. All tools automatically initialize the speaker connection.

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

### Music Search (2 tools)

#### `search_for_track <query>`
Search for music tracks by title, artist, or both.

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py search_for_track "Heart of Gold Neil Young"
```

**Returns:** Numbered list of matching tracks

#### `search_for_album <query>`
Search for music albums by title or artist.

**Usage:**
```bash
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py search_for_album "Harvest"
```

**Returns:** Numbered list of matching albums

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

## Common Workflows

These workflows demonstrate how to combine multiple tools for common tasks. Remember: The dispatcher path is long, so store it in a variable in your workflow for readability (if combining multiple calls).

### Search and Play a Track

**CRITICAL: To actually PLAY music, you need BOTH `add_track_to_queue` AND `play_from_queue`!**
Adding alone just queues the track - it doesn't start playback.

```bash
# Step 1: Search
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py search_for_track "Heart of Gold Neil Young"

# Step 2: Examine results, select position (let's say it's position 2)

# Step 3: Add to queue (does NOT start playing!)
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py add_track_to_queue 2

# Step 4: Check queue to find where it was added
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py list_queue

# Step 5: Play from that position (REQUIRED to start playback!)
# If queue shows 5 tracks, the newly added track is at position 5
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py play_from_queue 5
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
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py search_for_track "Neil Young"

# Add favorite track to playlist (position 3)
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py add_to_playlist_from_search my_mix 3

# Search for second artist
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py search_for_track "Bob Dylan"

# Add another track
/home/slzatz/sonos_mcp/.venv/bin/python3 /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code/sonos_tool.py add_to_playlist_from_search my_mix 1

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
