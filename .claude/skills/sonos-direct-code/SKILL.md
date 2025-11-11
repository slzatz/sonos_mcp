---
name: sonos-direct-code
description: "[DIRECT MODE - DEFAULT] Direct Python access to Sonos control via sonos_actions.py module. Use this skill for ALL Sonos requests when running in direct mode (default). Provides complete control through Python functions."
---

# Sonos Direct Code Access Skill

This skill provides guidance for directly importing and using the `sonos.sonos_actions` Python module for Sonos speaker control. Use this approach when you need flexibility, performance, or complex operations that don't fit the MCP tool model.

## Quick Start

**Always use this execution pattern:**
```bash
cd /home/slzatz/sonos_mcp && .venv/bin/python3 -c "
from sonos import sonos_actions

# Initialize speaker
sonos_actions.set_master()

# Use sonos_actions.function_name() - NEVER call methods on master directly
# Example:
queue = sonos_actions.list_queue()
for track in queue:
    print(f\"{track['title']} by {track['artist']}\")
"
```

**Critical Rules:**
1. Always `cd /home/slzatz/sonos_mcp` first (project root)
2. Use `.venv/bin/python3` (project's virtual environment)
3. **Only call functions from `sonos_actions` module**
4. **Never call methods on `master` object directly** (e.g., don't use `master.get_queue()`)
5. Always import: `from sonos import sonos_actions`
6. Always initialize: `sonos_actions.set_master()`

## Critical Workflow Rules

### MANDATORY Two-Step Workflow for Search Operations

**YOU MUST ALWAYS use a two-step approach when searching for and adding music:**

**CRITICAL: "Two-Step" means TWO SEPARATE BASH TOOL EXECUTIONS, not two commands in one script!**

**Why This Is Mandatory:**
- Search results are unpredictable and context-dependent
- The best match is **NOT always position 1**
- Artist name variations (Bill Callahan vs. Smog, for example)
- Multiple versions exist (remaster, live, cover, original, etc.)
- You MUST examine results before selecting which position to add
- **You cannot examine output if search and add are in the same Python script** - all code executes before you see any output!

**The Two-Step Pattern (TWO SEPARATE EXECUTIONS):**

**Step 1: FIRST BASH EXECUTION - Search ONLY**
```bash
cd /home/slzatz/sonos_mcp && .venv/bin/python3 -c "
from sonos import sonos_actions

sonos_actions.set_master()

# Search for the track - THIS IS ALL THIS EXECUTION DOES
results = sonos_actions.search_for_track('Bill Callahan The Breeze')
print(results)
"
```

**STOP HERE! Examine the output. DO NOT add anything yet.**

**Then:** Read the search results, identify which position is the best match, communicate your selection to the user.

**Step 2: SECOND BASH EXECUTION - Add ONLY**
```bash
cd /home/slzatz/sonos_mcp && .venv/bin/python3 -c "
from sonos import sonos_actions

sonos_actions.set_master()

# Add position 3 (YOU determined this from examining Step 1 output)
sonos_actions.add_track_to_queue(3)
print('Added track 3 to queue')
"
```

**Key Point:** These are TWO SEPARATE Bash tool calls. After the first one completes, you see the results, analyze them, then make the second call.

**Example - Correct Workflow for "Play a Track":**

User asks: "Play Bill Callahan's version of The Breeze"

**Step 1: Search**
```bash
cd /home/slzatz/sonos_mcp && .venv/bin/python3 -c "
from sonos import sonos_actions
sonos_actions.set_master()
results = sonos_actions.search_for_track('Bill Callahan The Breeze')
print(results)
"
```

**Step 2: Examine Results & Select**
Agent analyzes output: "Position 3 is specifically by Bill Callahan, that's the one!"

**Step 3: Add to Queue**
```bash
cd /home/slzatz/sonos_mcp && .venv/bin/python3 -c "
from sonos import sonos_actions
sonos_actions.set_master()
sonos_actions.add_track_to_queue(3)
print('Added track to queue')
"
```

**Step 4: Find Where It Was Added**
```bash
cd /home/slzatz/sonos_mcp && .venv/bin/python3 -c "
from sonos import sonos_actions
sonos_actions.set_master()
queue = sonos_actions.list_queue()
print(f'Queue has {len(queue)} tracks')
print(f'Newly added track is at position {len(queue)}')
"
```

**Step 5: Play from That Position**
```bash
cd /home/slzatz/sonos_mcp && .venv/bin/python3 -c "
from sonos import sonos_actions
sonos_actions.set_master()
queue = sonos_actions.list_queue()
# Play from the end of queue where track was just added
# play_from_queue uses 0-based indexing
sonos_actions.play_from_queue(len(queue) - 1)
print(f'Now playing track at end of queue')
"
```

**CRITICAL: When you add a track to the queue, it goes to the END of the queue, not position 0!**
- After adding a track, check queue length to find where it was added
- Play from that position (end of queue), NOT from position 0
- `play_from_queue()` uses 0-based indexing, so last track is `len(queue) - 1`

**Notice:** Multiple separate tool calls with analysis happening between them.

**NEVER Do This (Anti-Pattern):**
```bash
# ❌ WRONG - DO NOT DO THIS
cd /home/slzatz/sonos_mcp && .venv/bin/python3 -c "
from sonos import sonos_actions

sonos_actions.set_master()

# Search
results = sonos_actions.search_for_track('Bill Callahan The Breeze')

# Immediately add position 1 without examining results
sonos_actions.add_track_to_queue(1)  # ❌ WRONG - might not be the best match!
"
```

**Why the anti-pattern is wrong:**
- You haven't seen what position 1 actually is
- Position 1 might be a cover, live version, or wrong artist
- You're guessing instead of selecting based on actual results
- This defeats the purpose of having search results
- **Python executes ALL code before showing ANY output** - you can't "see" results mid-script
- By the time you see the printed results, the wrong track is already added!

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

## When to Use Direct Code Access

**Use this approach when:**
- Building complex workflows that chain multiple operations
- Need to process or analyze data (filter queue, analyze metadata)
- Performance is critical (no MCP protocol overhead)
- Creating one-off scripts or administrative tools
- Batch operations (e.g., converting all playlists)
- Development and debugging of new features

**Use MCP tools instead when:**
- Standard operations (play, search, volume control)
- Interactive conversation with users
- Need portability across AI platforms
- Working in Claude Desktop or other MCP clients

## Setup & Initialization

### Import and Initialize
```python
from sonos import sonos_actions

# Always initialize the master speaker first
sonos_actions.set_master()

# Or specify a different speaker
sonos_actions.set_master("Bedroom")
```

**Important:** The module uses a global `master` variable for the current speaker. Call `set_master()` before any operations.

## Recommended Functions (Current & Working)

### Speaker Management

#### `set_master(speaker=None) -> SoCo object or None`
Initialize or change the master speaker. Retries up to 3 times on failure.

**Parameters:**
- `speaker` (str, optional): Speaker name. If None, uses `master_speaker` from config.

**Returns:** SoCo speaker object or None on failure

**Example:**
```python
master = sonos_actions.set_master("Office2")
if master:
    print(f"Connected to {master.player_name}")
```

#### `check_master() -> bool`
Verify master speaker is connected. Attempts to reconnect if not.

### Playback Control

#### `current_track_info(text=True) -> str | dict | None`
Get information about currently playing track.

**Parameters:**
- `text` (bool): If True, returns formatted string. If False, returns dict.

**Returns:**
- `text=True`: "The track is {title}, the artist is {artist} and the album is {album}."
- `text=False`: `{'title': str, 'artist': str, 'album': str}`
- `None`: Nothing is playing

**Example:**
```python
# Get formatted string
info = sonos_actions.current_track_info(text=True)
print(info)  # "The track is Badlands, the artist is Bruce Springsteen..."

# Get structured data
track = sonos_actions.current_track_info(text=False)
if track:
    print(f"Now playing: {track['title']} by {track['artist']}")
```

#### `play_pause() -> None`
Toggle between play and pause states.

#### `play_from_queue(position) -> None`
Play track at specified position in queue (0-indexed).

**Parameters:**
- `position` (int): Queue position (0 = first track)

#### `playback(type_) -> None`
Generic playback control.

**Parameters:**
- `type_` (str): 'play', 'pause', 'stop', 'next', 'previous'

### Queue Management

#### `list_queue() -> List[dict]`
Get all tracks in the current queue.

**Returns:** List of track dictionaries:
```python
[
    {
        "title": "Badlands",
        "artist": "Bruce Springsteen",
        "album": "Darkness On the Edge of Town"
    },
    # ...
]
```

**Note:** Returns empty list if master is not connected. For MSTrack objects (music service tracks), album will be "(MSTrack)".

**Example:**
```python
queue = sonos_actions.list_queue()
for i, track in enumerate(queue, 1):
    print(f"{i}. {track['title']} - {track['artist']}")

# Filter for specific artist
springsteen = [t for t in queue if 'Springsteen' in t['artist']]
```

#### `clear_queue() -> None`
Remove all tracks from queue.

#### `remove_from_queue(position) -> None`
Remove track at position (1-indexed).

**Parameters:**
- `position` (int): Queue position (1 = first track)

#### `my_add_to_queue(uri, metadata) -> int`
Low-level function to add track to queue using DIDL metadata.

**Parameters:**
- `uri` (str): Track URI (can be empty string for some track types)
- `metadata` (str): DIDL-formatted XML metadata string

**Returns:** Queue position of added track (0 on failure)

**Note:** This is a low-level function. For most use cases, use `add_track_to_queue()` after searching.

### Music Search

#### `search_for_track(query) -> str`
Search for tracks and return formatted results.

**Parameters:**
- `query` (str): Search query (e.g., "Heart of Gold Neil Young")

**Returns:** Numbered list of results as string (e.g., "1. Heart of Gold-Neil Young-Harvest\n2. ...")

**Side Effects:**
- Saves results to `~/.sonos/search_results/track_search.json`
- This file is read by `add_track_to_queue()`

**Implementation Notes:**
- Uses Amazon Music search via SoCo MusicService
- Has retry logic for AuthTokenExpired errors (up to 5 retries)
- Has fallback search logic for parsing errors
- Returns up to ~46 results

**Example:**
```python
results = sonos_actions.search_for_track("neil young heart")
print(results)
# Display to user, then add track by position

# Results are cached, so you can add multiple tracks from same search
sonos_actions.add_track_to_queue(1)  # Add first result
sonos_actions.add_track_to_queue(5)  # Add fifth result
```

#### `search_for_album(query) -> str`
Search for albums and return formatted results.

**Parameters:**
- `query` (str): Album or artist name

**Returns:** Numbered list of results (e.g., "1. Harvest - Neil Young\n2. ...")

**Side Effects:**
- Saves results to `~/.sonos/search_results/album_search.json`
- This file is read by `add_album_to_queue()`

#### `add_track_to_queue(position) -> None`
Add track from search results to queue.

**Parameters:**
- `position` (int): Position in search results (1-indexed)

**Prerequisite:** Must call `search_for_track()` first to populate results file.

#### `add_album_to_queue(position) -> None`
Add album from search results to queue.

**Parameters:**
- `position` (int): Position in search results (1-indexed)

**Prerequisite:** Must call `search_for_album()` first to populate results file.

### Volume Control

#### `turn_volume(volume) -> None`
Adjust volume for all speakers in group.

**Parameters:**
- `volume` (str): 'louder' (increase by 10) or 'quieter' (decrease by 10)

**Example:**
```python
sonos_actions.turn_volume('louder')
sonos_actions.turn_volume('quieter')
```

#### `set_volume(level) -> None`
Set absolute volume level for all speakers in group.

**Parameters:**
- `level` (int): Volume level 0-100

#### `mute(bool_) -> None`
Mute or unmute all speakers in group.

**Parameters:**
- `bool_` (bool): True to mute, False to unmute

### Playlist Management

#### `list_playlists() -> str`
List all local playlists stored in `~/.sonos/playlists/`.

**Returns:** Formatted string with numbered list or error message.

**Example:**
```python
playlists = sonos_actions.list_playlists()
print(playlists)
# "Available playlists (4):
#  1. glenn_gould
#  2. favorites
#  ..."
```

#### `add_playlist_to_queue(playlist, shuffle=False) -> str`
Load entire local playlist into queue.

**Parameters:**
- `playlist` (str): Playlist filename (no path needed)
- `shuffle` (bool): If True, randomize track order before adding

**Returns:** Success message or error string

**Example:**
```python
# Add playlist in order
result = sonos_actions.add_playlist_to_queue('favorites')

# Add playlist shuffled
result = sonos_actions.add_playlist_to_queue('favorites', shuffle=True)
print(result)  # "Added 25 tracks from playlist favorites to the queue in random order"
```

#### `add_to_playlist_from_queue(playlist, position) -> str`
Add track from queue to a local playlist.

**Parameters:**
- `playlist` (str): Playlist filename (creates if doesn't exist)
- `position` (int): Queue position (1-indexed)

**Returns:** Success message with track details

**Example:**
```python
result = sonos_actions.add_to_playlist_from_queue('favorites', 3)
# "Selected track 3: Old Man by Neil Young from the queue and added to playlist favorites"
```

#### `add_to_playlist_from_search(playlist, position) -> str`
Add track from search results to a local playlist.

**Parameters:**
- `playlist` (str): Playlist filename
- `position` (int): Position in search results (1-indexed)

**Returns:** Success message with track details

**Prerequisite:** Must call `search_for_track()` first.

#### `get_native_sonos_playlists() -> str`
List all native Sonos playlists stored on Sonos system.

**Returns:** Formatted string with numbered list or error message

**Note:** These are different from local playlists - they're stored on Sonos and accessible from Sonos app.

**Example:**
```python
native = sonos_actions.get_native_sonos_playlists()
print(native)
# "Native Sonos playlists (3):
#  1. Every Single Day
#  2. Mighty Mean/Dreadful Sorrow
#  ..."
```

#### `create_native_playlist_from_local(local_playlist_name, native_playlist_name=None) -> str`
Convert local playlist to native Sonos playlist.

**Parameters:**
- `local_playlist_name` (str): Name of local playlist file
- `native_playlist_name` (str, optional): Name for native playlist (defaults to local name)

**Returns:** Success message or error string

**Implementation:**
- Checks for existing native playlist with same name
- Temporarily clears queue and loads local playlist
- Creates native playlist from queue
- Restores original queue

**Example:**
```python
result = sonos_actions.create_native_playlist_from_local('favorites', 'My Favorites')
print(result)
# "Successfully created native Sonos playlist 'My Favorites' from local playlist 'favorites'"
```

### Multi-Speaker Control

#### `unjoin() -> None`
Unjoin all speakers from the current group. Each becomes independent.

## Legacy/Deprecated Functions (Do Not Use)

### `shuffle(artists)` - Lines 483-520
**Status:** Deprecated, complex and unreliable

**Why avoid:** Uses old search patterns, has complex artist matching logic that often fails.

**Alternative:** Use `search_for_track()` with custom filtering instead.

### `old_shuffle(artists)` - Lines 522-548
**Status:** Completely broken

**Why avoid:** References undefined `solr` variable - this was from an old Solr search implementation.

**Alternative:** Use `search_for_track()` with Python's `random.shuffle()`.

### `current()` - Lines 550-565
**Status:** Replaced by better function

**Why avoid:** Returns raw SoCo track object, less useful than newer version.

**Alternative:** Use `current_track_info()` instead - cleaner return values.

### `extract(uri)` - Lines 567-575
**Status:** Unused, Spotify-specific

**Why avoid:** Only handles Spotify URIs, not used in current workflows.

### `play(add, uris)` - Lines 594-666
**Status:** Complex legacy function

**Why avoid:** Handles multiple URI types with complex DIDL formatting. Hard to use correctly.

**Alternative:** Use search → add → play workflow instead.

### `search_track_with_retry(track, max_retries=5)` - Lines 668-702
**Status:** Helper function (don't call directly)

**Why avoid:** Internal helper used by `search_for_track()`.

**Alternative:** Use `search_for_track()` which calls this internally.

### `search_track(track)` - Lines 704-727
**Status:** Older version

**Why avoid:** Returns different format than `search_for_track()`, saves to different file.

**Alternative:** Use `search_for_track()` instead (newer, better format).

### `play_track(track)` - Lines 729-734
**Status:** Too simple for most uses

**Why avoid:** Immediately plays first search result without user confirmation.

**Alternative:** Use `search_for_track()` → display results → `add_track_to_queue()` → `play_from_queue()`.

### `get_sonos_players()` - Lines 577-592
**Status:** Unused discovery function

**Why avoid:** Not integrated into current workflows, `set_master()` handles discovery.

**Alternative:** Use `set_master()` with speaker name.

### `play_station(station)` - Lines 142-151
**Status:** Limited functionality

**Why avoid:** Only works with predefined stations in `STATIONS` dict from config.

**Alternative:** Not commonly needed; if required, update `STATIONS` in `sonos_config.py` first.

## Common Workflows

### Search and Play
```python
from sonos import sonos_actions

# Initialize
sonos_actions.set_master()

# Search for music
results = sonos_actions.search_for_track("heart of gold neil young")
print(results)  # Show numbered list to user

# Add and play
sonos_actions.add_track_to_queue(1)  # Add first result
queue = sonos_actions.list_queue()
sonos_actions.play_from_queue(len(queue) - 1)  # Play last added track
```

### Build Custom Playlist
```python
from sonos import sonos_actions

sonos_actions.set_master()

artists = ["Neil Young", "Bob Dylan", "Tom Petty"]
playlist_name = "folk_rock_mix"

for artist in artists:
    results = sonos_actions.search_for_track(artist)
    # Add first 3 results from each artist
    for i in range(1, 4):
        try:
            sonos_actions.add_track_to_queue(i)
            queue = sonos_actions.list_queue()
            track = queue[-1]
            sonos_actions.add_to_playlist_from_queue(playlist_name, len(queue))
        except:
            continue

# Now play the playlist
sonos_actions.clear_queue()
sonos_actions.add_playlist_to_queue(playlist_name, shuffle=True)
sonos_actions.play_from_queue(0)
```

### Analyze Queue
```python
from sonos import sonos_actions
from collections import Counter

sonos_actions.set_master()
queue = sonos_actions.list_queue()

# Count tracks by artist
artists = [track['artist'] for track in queue]
artist_counts = Counter(artists)

print("Top artists in queue:")
for artist, count in artist_counts.most_common(5):
    print(f"  {artist}: {count} tracks")

# Find all tracks from specific album
album_tracks = [t for t in queue if t['album'] == 'Harvest']
print(f"\nTracks from Harvest: {len(album_tracks)}")
```

### Batch Convert Playlists to Native Sonos
```python
from sonos import sonos_actions

sonos_actions.set_master()

# Get all local playlists
playlists_str = sonos_actions.list_playlists()
# Parse the output to get playlist names (or maintain a list manually)

local_playlists = ["favorites", "workout", "chill"]

for playlist in local_playlists:
    result = sonos_actions.create_native_playlist_from_local(
        playlist,
        f"Claude_{playlist}"  # Prefix to distinguish
    )
    print(result)
```

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

## Error Handling

### Speaker Connection Issues
```python
master = sonos_actions.set_master()
if not master:
    print("Failed to connect to speaker after retries")
    # Handle error appropriately
```

### Queue Operations
```python
try:
    sonos_actions.clear_queue()
except Exception as e:
    print(f"Error clearing queue: {e}")
```

### Search Operations
The search functions have built-in retry logic for:
- `AuthTokenExpired` errors (retries up to 5 times)
- Parsing errors (tries fallback simplified searches)

## Important Notes

1. **Global State:** The module uses a global `master` variable. Always call `set_master()` first.

2. **Search Result Caching:** Search functions save results to files. Multiple adds from same search will read from the cached file.

3. **Queue Positions:**
   - `play_from_queue()`: 0-indexed (0 = first track)
   - `remove_from_queue()`: 1-indexed (1 = first track)
   - `add_to_playlist_from_queue()`: 1-indexed (1 = first track)

4. **DIDL Metadata:** Low-level functions like `my_add_to_queue()` require DIDL XML metadata strings. Use higher-level functions (search/add) instead.

5. **Music Service:** Configured in `sonos/config.py` as `music_service = "Amazon Music"`. Search results depend on this service.

6. **Multi-Speaker Groups:** Volume and mute operations affect all speakers in the master's group via `master.group.members`.

## Configuration

### `sonos/config.py` (User-created)
```python
master_speaker = "Office2"           # Default speaker name
music_service = "Amazon Music"       # Music service for searches
api_url = "https://genius.com/api"  # For lyrics (optional)
```

### `sonos/sonos_config.py` (In repository)
Contains DIDL templates and metadata formats. Generally don't need to modify.

## Execution

Always use the project virtual environment:

```bash
# From project root
.venv/bin/python3 -c "
from sonos import sonos_actions
# Your code here
"
```

Or in a script:
```python
#!/usr/bin/env python3
# Add project to path if needed
import sys
sys.path.insert(0, '/home/slzatz/sonos_mcp')

from sonos import sonos_actions

sonos_actions.set_master()
# ... rest of your code
```

## Dependencies

Key dependencies (from `sonos/sonos_actions.py`):
- `soco`: Sonos control library
- `unidecode`: Unicode normalization
- Standard library: `json`, `pathlib`, `random`, `html`, `urllib`, `ipaddress`

## When to Extend the MCP Server Instead

Consider adding a new MCP tool instead of direct code if:
- Operation will be used frequently in conversation
- Want it available in Claude Desktop
- Need user permission controls
- Operation is standardized (not one-off or experimental)

Then add function to `sonos_actions.py` AND wrap it as MCP tool in `sonos_mcp_server/server.py`.
