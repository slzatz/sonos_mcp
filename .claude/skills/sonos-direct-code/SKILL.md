---
name: sonos-direct-code
description: "[DIRECT MODE - DEFAULT] Sonos control via CLI dispatchers ONLY. NEVER import sonos_actions or write Python scripts - this bypasses architecture and is FORBIDDEN. ALL searches use Interactive TUI (mandatory). Use ONLY sonos_tool.py (23 tools: 19 Sonos + 4 TUI lifecycle) and tmux_tool.py (6 tools). If tools fail, REPORT error - never improvise workarounds."
---

# Sonos Direct Code Access Skill

This skill provides guidance for using the Sonos dispatcher tool (`sonos_tool.py`) for Sonos speaker control. The dispatcher exposes 23 active tools (19 Sonos tools + 4 TUI lifecycle management tools), all executing directly without protocol overhead for maximum token efficiency.

## ⚠️ CRITICAL: What You CANNOT Do

**NEVER do any of these - they violate the architecture:**

❌ **Import or call sonos_actions directly:**
```python
# FORBIDDEN - DO NOT DO THIS
from sonos import sonos_actions
python3 << 'EOF'
from sonos import sonos_actions
results = sonos_actions.search_for_track("query")
EOF
```

❌ **Write inline Python scripts to bypass dispatchers:**
```bash
# FORBIDDEN
python3 -c "from sonos import sonos_actions; ..."
```

❌ **Read source files to reverse-engineer APIs:**
```bash
# FORBIDDEN
cat /home/slzatz/sonos_mcp/sonos/sonos_actions.py
grep "def search" sonos/sonos_actions.py
```

❌ **Use CLI search tools (they don't exist):**
```bash
# FORBIDDEN - these tools are commented out
sonos_tool search_for_track "query"  # Does not exist
sonos_tool search_for_album "query"  # Does not exist
```

✅ **You MUST:**
- Use `sonos_tool` CLI for all Sonos operations
- Use Interactive TUI (via tmux) for ALL search operations
- Follow documented workflows exactly
- Report errors rather than improvising workarounds

**Why these restrictions exist:**
- Direct Python access defeats token optimization (~15% overhead)
- Bypassing tools breaks error handling and monitoring
- "Working" via wrong methods creates technical debt
- Architecture exists for performance and maintainability

**Remember:** A properly reported failure > a working workaround that violates architecture.

---

## Quick Start

### Two Approaches Available

**1. CLI Dispatcher Tools** (recommended for most operations):

**IMPORTANT: Use the Bash tool directly - DO NOT use tmux for CLI dispatcher commands!**

```bash
# Execute with Bash tool (NOT tmux)
sonos_tool <tool_name> [args...]
```

**2. Interactive TUI** (ONLY used to search for tracks or albums and place them on the queue):

**IMPORTANT: This is the ONLY use case for tmux tools (via tmux_tool.py dispatcher)!**

```bash
# Launch in tmux session (ONLY for interactive TUI)
sonos_tui
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
sonos_tool list_queue

# Set volume - use Bash tool
sonos_tool set_volume 50
```

**Key Features:**
- Speaker automatically initialized (no manual `set_master()` needed)
- All 23 tools available (19 Sonos tools + 4 TUI lifecycle) but don't use the CLI search tools, use the tmux TUI for searches
- Standardized error handling
- Results printed to stdout for agent inspection

### TUI Lifecycle Management

**NEW: Four convenience tools for managing the Interactive TUI**

Before working with the Interactive TUI (`sonos_interactive_tui.py`), use these tools to manage its lifecycle:

**1. Check if TUI is running:**
```bash
sonos_tool tui_status
```

Returns JSON with:
- `running`: true/false
- `status`: "running", "stopped", "not_running", or "stale"
- `current_prompt`: "search" or "select" (if running)
- `pid`: Process ID (if running)
- `pane_id`: tmux pane ID (if running)

**2. Start TUI in background:**
```bash
sonos_tool tui_start
```

- Automatically creates tmux session "sonos" if needed
- Launches TUI in the session
- Returns pane ID on success
- Returns error if TUI already running

**3. Stop TUI gracefully:**
```bash
sonos_tool tui_stop
```

- Sends quit command to TUI
- Waits up to 3 seconds for shutdown
- Returns success/failure status

**Recommended Workflow:**
1. Always call `tui_status` first to check if TUI is already running
2. If not running, call `tui_start` to launch it
3. Use tmux_tool.py for TUI interaction (send_keys, capture_pane)
4. **Use `tui_wait_for_prompt` after send_keys to wait for TUI readiness** (replaces sleep)
5. When done, optionally call `tui_stop` to clean up

**Example:**
```bash
# Step 1: Check status
/home/slzatz/sonos_mcp/.venv/bin/python3 .../sonos_tool.py tui_status
# Returns: {"running": false, "status": "not_running", ...}

# Step 2: Start TUI
/home/slzatz/sonos_mcp/.venv/bin/python3 .../sonos_tool.py tui_start
# Returns: "TUI started successfully on pane %0"

# Step 3: Interact via tmux_tool.py (see tmux-tool skill)
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "album: Nebraska"
# Wait for TUI to be ready (replaces sleep)
python3 .../sonos_tool.py tui_wait_for_prompt select  # Fast, reliable!
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 60

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
2. See results and select one or more matches (multi-selection supported)
3. Add to queue (automatically added, no playback prompt)
4. Loop back for more searches - all within a single running process
5. Agent uses `play_from_queue` for playback control

**Search Type Control:**
- **Track search (default):** Just enter your query (e.g., `Heart of Gold Neil Young`)
- **Album search:** Prefix query with `album:` (e.g., `album: Harvest Neil Young`)
  - **IMPORTANT:** Use `album:` with colon (preferred) or `album ` with space
  - Both formats work, but colon is preferred for clarity
  - Example: `album: Nebraska Bruce Springsteen` or `album Nebraska Bruce Springsteen`

The TUI automatically detects the prefix and uses the appropriate search and add functions.

**When to Use Track Search vs Album Search:**

Use **TRACK search** when:
- User specifies a number of songs ("3 tracks", "five songs", "a couple of tracks")
- User wants "best of" or curated selection ("best songs", "greatest hits", "top tracks")
- Building a varied queue with specific tracks
- User says "songs" or "tracks" (not "album")
- User wants cherry-picked selections from an artist's catalog

Use **ALBUM search** when:
- User explicitly says "play the album..."
- User wants complete album playback
- User mentions a specific album by name
- User wants the full artistic work as intended

**Examples:**
- "Put three Tom Petty songs on the queue" → **Track search**
- "Add some Aimee Mann best of tracks" → **Track search**
- "Play the album Harvest by Neil Young" → **Album search**
- "Add the Nebraska album" → **Album search**

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
Commands:
  - Search: Enter artist/track name (or 'album: artist/album name')
  - Select: Enter number(s) - single: '5' or multiple: '1 3 5'
  - No selection: Enter '0' to search again
  - Exit: Type 'quit'

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

**Step 4: Wait for TUI to show selection prompt**
```bash
# CRITICAL: Wait for TUI state transition - do NOT use sleep!
python3 sonos_tool tui_wait_for_prompt select
```

**Step 5: Capture search results**
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

Select track (1-50), multiple (e.g., '1 3 5'), or 0 for no selection:
```

**Step 6: Analyze results and send selection**

Examine the results and pick the best match. Send one or more item numbers (track or album):

```bash
# Single selection
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "1"

# Multi-selection (space-separated numbers)
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "1 3 5"

# No selection (return to search)
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "0"
```

**Step 7: Wait for return to search prompt**
```bash
# CRITICAL: Wait for TUI state transition - do NOT use sleep!
python3 sonos_tool tui_wait_for_prompt search
```

**Step 8: Capture queue confirmation**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 20
```

You'll see:
```
Adding track 1 to queue...
Track added at position 12.

================================================================================

Search:
```

**Step 9: Loop continues or use play_from_queue**

The TUI returns to search prompt. You can:
- Search for more tracks
- Exit TUI with "quit"
- Use `sonos_tool play_from_queue 12` to start playback from position 12

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
- **Track/Album number(s)** (at "Select:" prompt)
  - Single selection: `1`
  - Multi-selection: `1 3 5` (space-separated numbers)
  - No selection: `0` (returns to search)
- **"quit"** (ONLY at Search prompt - exits TUI completely)

**CRITICAL: '0' vs 'quit' Usage:**
- At **Selection prompt**: Use `"0"` to skip selection and return to search
  - ❌ DO NOT send "quit" or "q" at selection prompt - will cause error
  - ✅ Send "0" to go back to search
- At **Search prompt**: Use `"quit"` to exit the TUI completely
  - ✅ Send "quit" when done with all searches
  - Also accepts "q" or "exit" at search prompt

**Example - Correct usage:**
```bash
# At search prompt
send_keys %0 "Patty Griffin"
wait_for_prompt select
capture_pane %0
# At selection prompt - decide not to select
send_keys %0 "0"  # ✓ Returns to search
# NOT: send_keys %0 "quit"  # ✗ Would cause error

# At search prompt - done with TUI
send_keys %0 "quit"  # ✓ Exits TUI
```

### Selection Best Practices

**IMPORTANT: Making Smart Selections from Search Results**

When the TUI displays search results, you must analyze them carefully and make informed selections:

**DO:**
- ✅ **Review ALL search results** before selecting
- ✅ **Look for tracks from "Greatest Hits", "Best Of", or compilation albums** when user wants best-of selections
- ✅ **Consider track relevance**: Is this a well-known hit? Does it match what the user asked for?
- ✅ **Explain your reasoning** before making selections (e.g., "I'll select positions 1, 5, and 23 because they're from Greatest Hits albums")
- ✅ **Use thoughtful selection patterns** based on the actual results shown

**DON'T:**
- ❌ **Never select numbers just because they're sequential** (1 2 3) or from an example
- ❌ **Don't ignore album information** - "Greatest Hits" albums often contain the best matches
- ❌ **Don't select blindly** - actually read the artist, title, and album names
- ❌ **Don't rush** - take time to identify the best matches

**Selection Reasoning (Mandatory):**

Before sending your selection to the TUI, you MUST explain your reasoning to the user. This ensures transparency and correct selections.

**Example workflow:**
```
# After capturing search results showing 50 Tom Petty tracks
User request: "Put three Tom Petty best of songs on the queue"

# Your analysis (show to user):
"I found 50 Tom Petty tracks. Reviewing the results:
- Position 1: 'Free Fallin'' - Tom Petty and the Heartbreakers - Full Moon Fever (iconic hit)
- Position 5: 'American Girl' - Tom Petty and the Heartbreakers - Tom Petty Greatest Hits (from best-of album)
- Position 43: 'Learning to Fly' - Tom Petty and the Heartbreakers - Greatest Hits (from best-of album)

I'll select tracks 1, 5, and 43 because they're well-known hits, with positions 5 and 43
specifically from Greatest Hits albums."

# Then send selection
send_keys %0 "1 5 43"
```

**Pattern Recognition - What NOT to do:**

❌ **Bad: Following examples blindly**
```
# User: "Put three Aimee Mann songs on queue"
# Search shows 50 results
# Agent thinks: "The prompt says '1 3 5' as an example, I'll use that"
send_keys %0 "1 3 5"  # ✗ Blind pattern-matching!
```

✅ **Good: Analyzing results intelligently**
```
# User: "Put three Aimee Mann songs on queue"
# Search shows 50 results
# Agent captures results, reviews them, and explains:
"I found 50 Aimee Mann tracks. Looking at the results:
- Position 1: 'Save Me' - from Magnolia soundtrack (well-known hit)
- Position 8: 'Wise Up' - from Magnolia (another iconic track)
- Position 15: 'Save Me' - from Ultimate Collection (best-of version)

I'll select 1, 8, and 15 because they're her most recognizable songs."
send_keys %0 "1 8 15"  # ✓ Thoughtful selection!
```

### TUI Lifecycle - Best Practices

**Default Behavior: Keep Running**

The TUI is designed for **continuous use** across multiple user requests. After completing searches:
- ✅ **Leave TUI running** (do NOT call tui_stop)
- ✅ TUI stays ready for next search request
- ✅ No restart overhead for subsequent searches
- ✅ Preserves stateful session context

**Only Stop TUI When:**
1. **User explicitly says they're done**: "that's all", "I'm done", "stop the TUI"
2. **TUI encounters errors**: Use tui_stop → tui_start to restart
3. **User directly requests it**: "please stop the TUI"

**Anti-Pattern - Starting and Stopping Each Time:**
```bash
# ❌ INEFFICIENT - Don't do this
# Request 1:
tui_start
send_keys %0 "Jackson Browne"
[select tracks]
tui_stop  # ❌ Unnecessary!

# Request 2 (user asks for more songs):
tui_start  # ❌ Wasteful restart
send_keys %0 "Neil Young"
[select tracks]
tui_stop  # ❌ Still running/stopping unnecessarily
```

**Correct Pattern - Leave Running:**
```bash
# ✅ EFFICIENT - Do this
# Request 1:
tui_start
send_keys %0 "Jackson Browne"
[select tracks]
# Leave running...

# Request 2 (user asks for more songs):
# No restart needed! TUI already running
send_keys %0 "Neil Young"
[select tracks]
# Leave running...

# User: "that's all for now"
tui_stop  # ✓ Only stop when actually done
```

**Benefits of Keeping TUI Running:**
- **Performance**: No tui_start overhead for each request (~1-2 seconds saved)
- **Statefulness**: Maintains session context
- **Simplicity**: One less tool call per request
- **Natural**: Matches how humans use TUI applications

### CRITICAL: CLI Dispatcher Commands Work Independently of TUI

**You can run CLI dispatcher commands via Bash tool while the TUI is running!**

The TUI and CLI dispatcher are completely independent:
- **TUI**: Runs in tmux session for search operations
- **CLI dispatcher**: Executed via Bash tool for all other operations (queue, volume, playback, playlists)
- **They do NOT interfere with each other**

**Anti-Pattern - Unnecessary TUI Quitting:**
```bash
# ❌ WRONG - Don't quit TUI to run CLI commands
tui_start
send_keys %0 "Ani DiFranco"
wait_for_prompt select
capture_pane %0
send_keys %0 "1 4 6 16"
wait_for_prompt search
capture_pane %0
send_keys %0 "quit"           # ❌ Unnecessary quit!
sonos_tool list_queue         # ❌ Could have done this while TUI was running!
```

**Correct Pattern - Keep TUI Running:**
```bash
# ✅ CORRECT - Use Bash tool for CLI commands while TUI stays running
tui_start
send_keys %0 "Ani DiFranco"
wait_for_prompt select
capture_pane %0
send_keys %0 "1 4 6 16"
wait_for_prompt search
capture_pane %0
# TUI stays at search prompt - ready for next search
# Meanwhile, use Bash tool for other operations:
sonos_tool list_queue         # ✅ Works fine! TUI still running
sonos_tool play_from_queue 15 # ✅ Playback control via Bash
sonos_tool set_volume 40      # ✅ Volume control via Bash
# TUI is STILL RUNNING and ready for the next search!
```

**When to Use Each Tool:**
- **TUI (via tmux tools)**: ONLY for search operations (track/album search and selection)
- **CLI dispatcher (via Bash)**: For everything else (queue, volume, playback, playlists, current track, etc.)
- **Both can be used simultaneously** - they are independent processes

**Why This Matters:**
- **Efficiency**: No need to quit/restart TUI between operations
- **Simplicity**: Just use Bash tool for non-search commands
- **Performance**: Saves 1-2 seconds per operation (no TUI restart)
- **Correctness**: TUI stays ready for next search request

**Remember:** Unless the user explicitly says "quit the TUI" or "I'm done searching", keep it running!

### TUI vs CLI Dispatcher Comparison

| Feature | Interactive TUI | CLI Dispatcher |
|---------|----------------|----------------|
| **Process lifecycle** | Runs continuously | Tool invoked per operation |
| **State** | Maintains state | Stateless (reads from files) |
| **Search workflow** | Integrated (search → select) | No search capability |
| **Playback control** | No (use play_from_queue) | Yes (play_from_queue, play_pause, etc.) |
| **Multi-selection** | Yes (e.g., "1 3 5") | N/A |
| **Used for** | Searches, queue building | ALL other tasks (incl. playback) |
| **Uses tmux** | Yes | No |
| **Control flow** | Sequential prompts | Explicit tool selection |

### TUI Implementation Details

**File Location:** `sonos_tui`

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

**Known Issue - Amazon Music Authorization (Transient):**

Amazon Music API occasionally returns "Authorization expired" errors even when authorization is valid. This is a **known transient glitch**, not a real problem.

**Symptoms:**
- Search returns "Authorization expired" error
- Error occurs randomly, not consistently
- Authorization is actually valid

**Solution - Automatic Retry:**
```bash
# First attempt
send_keys %0 "Patty Griffin"
wait_for_prompt select
capture_pane %0
# If you see "Authorization expired" in output:

# Simply retry immediately (usually succeeds)
send_keys %0 "0"  # Go back to search
wait_for_prompt search
send_keys %0 "Patty Griffin"  # Same search again
wait_for_prompt select
capture_pane %0  # Usually works now
```

**Best Practice:**
- If you see "Authorization expired": Retry once immediately
- Do NOT report it as a real authorization problem
- Do NOT try to re-authenticate
- Usually resolves on second attempt (1-2 seconds later)
- Only report if it persists after 2-3 retries

**Features:**
- Clear prompts designed for tmux capture
- Error handling with user-friendly messages
- Automatic speaker initialization on startup
- Queue position tracking for accurate playback

### Example: Building a Queue with TUI

Here's a complete example of using the TUI to build a queue with multiple tracks and multi-selection:

```bash
# Step 0: Ensure "sonos" tmux session exists and launch TUI
# Use tui_start (recommended - handles everything):
python3 sonos_tool tui_start
# Returns: "TUI started successfully on pane %0"

# OR manual approach with tmux_tool.py:
python3 .claude/skills/tmux-tool/tmux_tool.py session_ready sonos  # Get pane ID
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "cd /home/slzatz/sonos_mcp/.claude/skills/sonos-direct-code && /home/slzatz/sonos_mcp/.venv/bin/python3 sonos_interactive_tui.py"

# Search for Bruce Springsteen tracks
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "Bruce Springsteen"

# CRITICAL: Wait for selection prompt (do NOT use sleep!)
python3 sonos_tool tui_wait_for_prompt select

# Capture results
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0

# Multi-select three great tracks
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "2 5 8"

# Wait for return to search
python3 sonos_tool tui_wait_for_prompt search

# Search for an album (note the "album:" prefix)
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "album: Harvest Neil Young"

# Wait for selection prompt
python3 sonos_tool tui_wait_for_prompt select

# Capture album results
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0

# Select album 1
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "1"

# Wait for return to search
python3 sonos_tool tui_wait_for_prompt search

# Search for Leonard Cohen
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "Leonard Cohen"

# Wait for selection prompt
python3 sonos_tool tui_wait_for_prompt select

# Capture results
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0

# Multi-select two tracks
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "1 4"

# Wait for return to search
python3 sonos_tool tui_wait_for_prompt search

# Exit TUI
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "quit"

# Now use CLI dispatcher to check queue and start playback
python3 sonos_tool list_queue
# Agent determines first new position (let's say it was 10)
python3 sonos_tool play_from_queue 10
```

This builds a queue with multi-selected tracks and a full album, then uses `play_from_queue` for playback control. The example demonstrates:
- Multi-selection efficiency (one search for multiple Bruce Springsteen tracks)
- Mixing track searches with album searches using the `album:` prefix
- Separation of concerns (TUI for search/selection, CLI dispatcher for playback)

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

## Available Tools (23 Total)

The dispatcher provides these tools. Most tools automatically initialize the speaker connection (TUI lifecycle tools do not require speaker connection).

**IMPORTANT:** There are NO CLI search tools - ALL searches must use the Interactive TUI!

### Speaker Management (2 tools)

#### `get_master_speaker`
Get the currently configured master speaker name.

**Usage:**
```bash
sonos_tool get_master_speaker
```

#### `set_master_speaker <speaker_name>`
Change the master speaker to a different Sonos device.

**Usage:**
```bash
sonos_tool set_master_speaker "Bedroom"
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
sonos_tool list_queue
```

#### `add_track_to_queue <position>`
Add track from search results to queue (1-indexed position).

**IMPORTANT: This tool ONLY adds to queue - it does NOT start playback!**
You must call `play_from_queue` separately to play the track.

**Usage:**
```bash
sonos_tool add_track_to_queue 1
```

**No flags/options:** This tool takes only the position number - no `--play` or other flags exist.

#### `add_album_to_queue <position>`
Add album from search results to queue (1-indexed position).

**Usage:**
```bash
sonos_tool add_album_to_queue 1
```

#### `clear_queue`
Clear all tracks from the current queue.

**Usage:**
```bash
sonos_tool clear_queue
```

#### `remove_from_queue <position>`
Remove track from queue by position (1-indexed).

**Usage:**
```bash
sonos_tool remove_from_queue 3
```

#### `play_from_queue <position>`
Play track from queue by position (1-indexed).

**Usage:**
```bash
sonos_tool play_from_queue 1
```

### Playback Control (3 tools)

#### `current_track`
Get information about what's currently playing.

**Usage:**
```bash
sonos_tool current_track
```

#### `play_pause`
Toggle play/pause of the current track.

**Usage:**
```bash
sonos_tool play_pause
```

#### `next_track`
Skip to the next track in the queue.

**Usage:**
```bash
sonos_tool next_track
```

### Volume Control (3 tools)

#### `turn_volume <direction>`
Adjust volume up or down by 10 (`louder` or `quieter`).

**Usage:**
```bash
sonos_tool turn_volume louder
sonos_tool turn_volume quieter
```

#### `set_volume <level>`
Set absolute volume level (0-100).

**Usage:**
```bash
sonos_tool set_volume 50
```

#### `mute <true|false>`
Mute or unmute all speakers in the group.

**Usage:**
```bash
sonos_tool mute true
sonos_tool mute false
```

### Playlist Management (5 tools)

#### `list_playlists`
List all available local playlists.

**Usage:**
```bash
sonos_tool list_playlists
```

#### `add_to_playlist_from_queue <playlist> <position>`
Add track from queue to a playlist (position is 1-indexed).

**Usage:**
```bash
sonos_tool add_to_playlist_from_queue favorites 3
```

#### `add_to_playlist_from_search <playlist> <position>`
Add track from search results to a playlist (position is 1-indexed).

**Usage:**
```bash
sonos_tool add_to_playlist_from_search favorites 1
```

#### `add_playlist_to_queue <playlist> [shuffle]`
Load playlist to queue. Optional `shuffle` parameter (true/false).

**Usage:**
```bash
sonos_tool add_playlist_to_queue favorites
sonos_tool add_playlist_to_queue favorites true
```

#### `list_playlist_tracks <playlist>`
Display all tracks in a saved playlist.

**Usage:**
```bash
sonos_tool list_playlist_tracks favorites
```

#### `remove_track_from_playlist <playlist> <position>`
Remove track from playlist by position (1-indexed).

**Usage:**
```bash
sonos_tool remove_track_from_playlist favorites 5
```

#### `list_native_sonos_playlists`
List all native Sonos playlists stored on the Sonos system.

**Usage:**
```bash
sonos_tool list_native_sonos_playlists
```

#### `create_native_sonos_playlist_from_local <local_playlist> [native_name]`
Create native Sonos playlist from local playlist file.

**Usage:**
```bash
sonos_tool create_native_sonos_playlist_from_local favorites "My Favorites"
```

### TUI Lifecycle Management (4 tools)

These tools manage the Interactive TUI (`sonos_interactive_tui.py`) process lifecycle. Unlike other tools, these do NOT require speaker initialization.

#### `tui_status`
Check if the Interactive TUI is running and get its current state.

**Usage:**
```bash
sonos_tool tui_status
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
sonos_tool tui_start
```

**Behavior:**
- Creates tmux session "sonos" if it doesn't exist
- Launches TUI in that session's first pane
- Waits 1 second for initialization
- Verifies TUI started successfully
- Returns pane ID (e.g., "%0") on success
- Returns error if TUI already running

**IMPORTANT - No Sleep Needed:**
When `tui_start` returns successfully, the TUI is **guaranteed ready** for immediate use. Do NOT add additional sleep or status checks:
- ❌ WRONG: `tui_start` then `sleep 2 && tui_status` (unnecessary!)
- ✅ CORRECT: `tui_start` then immediately use TUI (it's already verified!)

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
sonos_tool tui_stop
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

#### `tui_wait_for_prompt <expected_prompt> [timeout]`
Wait for the TUI to reach a specific prompt state.

**IMPORTANT: Use this instead of fixed sleep times for faster, more reliable TUI interactions!**

This tool efficiently polls the TUI state file (`~/.sonos/tui_state.json`) instead of using fixed sleep times. The TUI updates its state at key transitions (search → select → search), allowing the agent to know exactly when the TUI is ready for next input.

**Usage:**
```bash
sonos_tool tui_wait_for_prompt select
sonos_tool tui_wait_for_prompt search 3.0
```

**Parameters:**
- `expected_prompt`: One of `search`, `select` (required)
- `timeout`: Optional timeout in seconds (default: 5.0)

**How it works:**
- Polls state file every 100ms (10x per second)
- Returns immediately when TUI reaches expected prompt
- Provides actual wait time in success message
- Reports current prompt in timeout message for debugging

**Example workflow (replaces sleep):**

Old way (slow, unpredictable):
```bash
send_keys "album: Harvest Moon"
sleep 2 && capture_pane        # Fixed 2 second wait - might be too long or too short!
```

New way (fast, reliable):
```bash
send_keys "album: Harvest Moon"
tui_wait_for_prompt "select"   # Waits only as long as needed (typically 100-500ms)
capture_pane
```

**Complete example:**
```bash
# Send search query
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "album: Nebraska"

# Wait for TUI to show selection prompt (100-500ms typically)
python3 .claude/skills/sonos-direct-code/sonos_tool.py tui_wait_for_prompt select
# Returns: "TUI ready at 'select' prompt (waited 0.23s)"

# Now capture results
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0

# Send selection (single or multi-select)
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "1"

# Wait for return to search (100-200ms typically)
python3 .claude/skills/sonos-direct-code/sonos_tool.py tui_wait_for_prompt search
# Returns: "TUI ready at 'search' prompt (waited 0.12s)"
```

**Benefits:**
- **2-3x faster** than fixed sleeps (200-700ms total vs 2-3 seconds)
- **More reliable** - waits exactly until ready, not too short or too long
- **Predictable** - agent doesn't have to guess sleep times
- **Self-documenting** - shows actual wait time for diagnostics

**Error handling:**
```bash
# If timeout (default 5 seconds):
Timeout waiting for 'select' prompt (currently at: 'search', waited 5.0s)
```

**When to use:**
- **After every send_keys to TUI** - replaces all `sleep && capture_pane` patterns
- Between TUI state transitions (search → select → search)
- Before capturing pane to ensure TUI has updated display

**Valid prompt values:**
- `search` - TUI is at "Search:" prompt
- `select` - TUI is at "Select track/album (1-N), multiple, or 0:" prompt

## Common Workflows

**⚠️ CRITICAL - TUI Timing:**
- **ALWAYS use `tui_wait_for_prompt` after `send_keys`** - never use sleep!
- Pattern: `send_keys` → **`tui_wait_for_prompt`** → `capture_pane`
- Sleep is slow (1-2s fixed) and unreliable
- `tui_wait_for_prompt` is fast (100-500ms) and reliable
- See `tui_wait_for_prompt` documentation above for details

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
Commands:
  - Search: Enter artist/track name (or 'album: artist/album name')
  - Select: Enter number(s) - single: '5' or multiple: '1 3 5'
  - No selection: Enter '0' to search again
  - Exit: Type 'quit'

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

**Step 4: Wait for TUI to show selection prompt**
```bash
# CRITICAL: Wait for TUI state transition - do NOT use sleep!
python3 sonos_tool tui_wait_for_prompt select
```

**Step 5: Capture search results**
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

Select track/album (1-50), multiple (e.g., '1 3 5'), or 0 for no selection:
```

**Step 6: Analyze results and send selection**

Examine the results and pick the best match. Send one or more item numbers (track or album):

```bash
# Single selection
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "3"

# Or multi-selection
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "2 5 8"
```

**Step 7: Wait for return to search prompt**
```bash
# CRITICAL: Wait for TUI state transition - do NOT use sleep!
python3 sonos_tool tui_wait_for_prompt search
```

**Step 8: Capture queue confirmation**
```bash
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 20
```

You'll see:
```
Adding track 3 to queue...
Track added at position 12.

================================================================================

Search:
```

**Step 9: Use play_from_queue for playback**

The TUI has added the track to the queue. Now use the CLI dispatcher for playback:

```bash
# Play from the position where track was added
python3 sonos_tool play_from_queue 12

# Or continue searching and quit TUI
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "quit"
```

### Load and Play a Playlist

```bash
# Clear existing queue
sonos_tool clear_queue

# Add playlist (shuffled)
sonos_tool add_playlist_to_queue favorites true

# Play first track
sonos_tool play_from_queue 1
```

### Build a Custom Playlist from Searches

```bash
# Search for first artist
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "Joan Baez"

# Wait for selection prompt
python3 sonos_tool tui_wait_for_prompt select

# Capture results
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 50

# Select first result
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "1"

# Wait for return to search
python3 sonos_tool tui_wait_for_prompt search

# Add track to playlist from queue (assuming it's at position 1)
sonos_tool add_to_playlist_from_queue my_mix 1

# Search for second artist
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "Bob Dylan"

# Wait for selection prompt
python3 sonos_tool tui_wait_for_prompt select

# Capture results
python3 .claude/skills/tmux-tool/tmux_tool.py capture_pane %0 50

# Select first result
python3 .claude/skills/tmux-tool/tmux_tool.py send_keys %0 "1"

# Wait for return to search
python3 sonos_tool tui_wait_for_prompt search

# Add track to playlist from queue (assuming it's at position 2)
sonos_tool add_to_playlist_from_queue my_mix 2

# View the playlist
sonos_tool list_playlist_tracks my_mix
```

### Check What's Playing and Control Playback

```bash
# Get current track
sonos_tool current_track

# Pause
sonos_tool play_pause

# Adjust volume
sonos_tool turn_volume louder

# Skip to next
sonos_tool next_track
```

### Create Native Sonos Playlist from Local

```bash
# List local playlists
sonos_tool list_playlists

# Convert to native Sonos playlist
sonos_tool create_native_sonos_playlist_from_local favorites "My Favorite Songs"

# Verify it was created
sonos_tool list_native_sonos_playlists
```

## Important Notes

1. **Tool Path:** The dispatcher tool is located at `sonos_tool` and must be called with the project's venv Python: `/home/slzatz/sonos_mcp/.venv/bin/python3`

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
