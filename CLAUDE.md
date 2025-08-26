# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure

This is a Python CLI application for controlling Sonos speakers. Key components:

- **sonos/cli.py**: Main CLI interface using Click framework with command definitions
- **sonos/sonos_actions.py**: Core Sonos functionality using the SoCo library to interact with speakers
- **sonos/config.py**: Configuration file containing API keys and service endpoints  
- **sonos/sonos_config.py**: Sonos-specific configuration (station definitions, metadata templates)
- **sonos/get_lyrics.py**: Lyrics retrieval from Genius API using cloudscraper

## Architecture

The application follows a layered architecture:
1. CLI layer (cli.py) handles user input and command parsing
2. Action layer (sonos_actions.py) implements Sonos control logic
3. Configuration layer provides service endpoints and settings

The main entry point is the `sonos` command defined in pyproject.toml that maps to `sonos.cli:cli`.

## Key Dependencies

- **soco**: Python library for controlling Sonos speakers
- **click**: Command line interface framework
- **cloudscraper**: Web scraping with CloudFlare bypass
- **unidecode**: Unicode text handling

## Common Commands

Install dependencies:
```bash
uv sync
```

Install the CLI tool in development mode:
```bash
uv pip install -e .
```

Run the CLI:
```bash
sonos --help
```

The CLI supports master speaker selection with `-m/--master` and verbose output with `-v/--verbose`.

## Music Service Integration

The application integrates with Amazon Music as the primary music service (configured in config.py). It handles different URI formats for:
- Amazon Music catalog tracks
- Spotify tracks  
- Amazon Music library tracks
- Local playlists
- Radio stations (Pandora, WNYC, etc.)

## Key Functions

- **play_track()**: Search and play individual tracks
- **shuffle()**: Create shuffled playlists from artist searches
- **play_album()**: Play complete albums
- **play_station()**: Play predefined radio stations
- **current_track_info()**: Get information about currently playing track

## Claude Code Integration for Music Requests

When users make natural language music requests like "play harvest by neil young", Claude Code should use this two-step workflow:

### 1. Search for Tracks
```bash
sonos searchtrack harvest by neil young
```

This returns a numbered list of search results in the format:
```
1. Harvest Moon-Neil Young-Harvest Moon
2. Harvest (2009 Remaster)-Neil Young-Harvest (2009 Remaster)
3. Heart of Gold-Neil Young-Harvest
4. Harvest-Neil Young-Harvest
5. Harvest (Live)-Neil Young & Stray Gators-Tuscaloosa (Live)
...
```

### 2. Select and Play Best Match
```bash
sonos playtrackfromlist 4
```

Uses the position number (1-indexed) to play the selected track.

### Search Result Analysis

The search results are stored in `sonos_track_uris.json` and display as:
- **Format**: `number. Title-Artist-Album`
- **Parsing**: Split on `-` to separate title, artist, and album
- **Matching**: Look for exact title matches, then fuzzy matches
- **Album-Aware Live Detection**: Identifies live versions from album names like "Live from the Artists Den", "Tuscaloosa (Live)", etc.
- **Preferences**: 
  - Exact title matches over partial matches
  - When live versions requested: Boost tracks from live albums
  - When studio versions preferred: Prefer studio albums over remasters/live versions
  - Artist name matching for disambiguation
  - Album context for enhanced live version detection

### Smart Selection Logic

For the request "play harvest by neil young":
1. Look for exact title match "Harvest" by "Neil Young"
2. Prefer original over "(2009 Remaster)" or "Live" versions
3. If multiple exact matches exist, select the first non-remastered version
4. If no exact matches, use fuzzy matching on title similarity

### Example Workflow

User request: "play harvest by neil young"
1. Execute: `sonos searchtrack harvest by neil young`
2. Parse results and identify "4. Harvest-Neil Young" as best match
3. Execute: `sonos playtrackfromlist 4`
4. Confirm: "Playing Harvest by Neil Young"

### Common Commands for Claude Code

- Search: `sonos searchtrack <query>`
- Play from list: `sonos playtrackfromlist <number>`
- Current track: `sonos what`
- Pause/Resume: `sonos pause` / `sonos resume`
- Volume: `sonos louder` / `sonos quieter`
- Queue: `sonos showqueue`

## Helper Functions

The `sonos_helpers.py` module provides utility functions for Claude Code to process music requests:

### Key Functions

- **parse_search_results(output)**: Parse sonos searchtrack output into structured data with album information
- **find_best_match(results, title, artist, preferences)**: Find the best matching track using smart algorithms with album-aware live detection
- **extract_music_request(input)**: Extract title, artist, and preferences from natural language requests
- **execute_smart_search(title, artist, preferences)**: Multi-search strategy with intelligent query variations
- **handle_music_request(input)**: Complete end-to-end workflow for processing music requests
- **clean_title(title)**: Remove remasters, live tags, and other annotations
- **similarity_score(str1, str2)**: Calculate string similarity for fuzzy matching

### Usage Examples

#### Basic Music Request
```python
from sonos_helpers import handle_music_request

# Simple one-step workflow
position = handle_music_request("play harvest by neil young")
# Returns: position to play (e.g., 4)

if position:
    subprocess.run(['sonos', 'playtrackfromlist', str(position)])
```

#### Advanced Workflow with Live Version Preference
```python
from sonos_helpers import extract_music_request, execute_smart_search

# Extract request with preferences
title, artist, preferences = extract_music_request("play a live version of harvest by neil young")
# Returns: ("harvest", "neil young", {"prefer_live": True})

# Execute smart search with multiple query attempts
position = execute_smart_search(title, artist, preferences)
# Tries: "live harvest neil young", "harvest live neil young", etc.
# Returns: position of best live version match
```

#### Manual Step-by-Step
```python
from sonos_helpers import parse_search_results, find_best_match, extract_music_request

# Extract request components
title, artist, preferences = extract_music_request("play harvest by neil young")
# Returns: ("harvest", "neil young", {})

# After running sonos searchtrack
results = parse_search_results(search_output)
# Returns: [(1, "Harvest Moon", "Neil Young", "Harvest Moon"), (2, "Harvest", "Neil Young", "Harvest"), ...]

# Find best match with preferences (now album-aware)
position = find_best_match(results, title, artist, preferences)
# Returns: 2 (for exact "Harvest" match from studio album)
```

### Integration Workflow for Claude Code

#### Option 1: Simple One-Step Workflow (Recommended)
```python
from sonos_helpers import handle_music_request
import subprocess

position = handle_music_request(user_request)
if position:
    subprocess.run(['sonos', 'playtrackfromlist', str(position)])
    # Confirm what's playing with: sonos what
```

#### Option 2: Advanced Multi-Search Workflow
1. **Parse User Request**: Use `extract_music_request()` to get title, artist, and preferences
2. **Execute Smart Search**: Use `execute_smart_search()` which tries multiple query variations
3. **Play Track**: Execute `sonos playtrackfromlist <position>`
4. **Confirm**: Show user what's playing

### Enhanced Features

#### Live Version Detection
The system now detects requests for live versions using patterns like:
- "play a live version of harvest by neil young"
- "live recording of harvest neil young" 
- "concert version of harvest"
- "harvest live neil young"

When live versions are requested, the system:
1. **Tries live-specific searches first**: "live harvest neil young", "harvest live neil young"
2. **Album-aware live detection**: Identifies live recordings from album names using patterns:
   - "live from", "live at", "concert", "acoustic", "unplugged", "artists den"
3. **Enhanced scoring**: Live tracks get +0.3 score bonus when requested
4. **Smart fallback**: Falls back to studio versions if no live matches found

#### Multi-Search Strategy
For complex requests, the system tries multiple search queries:
- Base query: "harvest by neil young"
- Live variants: "live harvest neil young", "harvest live neil young", "neil young harvest live"
- Selects best match across all search attempts

#### Album-Aware Live Detection Example

Request: "play a live version of burgundy shoes by patty griffin"

Search results:
```
1. Burgundy Shoes-Patty Griffin-Children Running Through
2. Burgundy Shoes-Patty Griffin-Patty Griffin: Live from the Artists Den
```

The system detects that "Live from the Artists Den" indicates a live album and selects position 2, even though the track title doesn't contain "live".

This approach handles variations like remasters, live versions, and fuzzy title matching while intelligently preferring the requested version type using both track titles and album context.

## Known Issues

### Amazon Music API Search Parsing Error
Some specific search terms trigger a parsing error in the SoCo library:
- **Error**: `TypeError: string indices must be integers, not 'str'`
- **Cause**: Amazon Music API returns malformed responses for certain search combinations
- **Example**: `sonos searchtrack "fixing her hair"` fails, but `sonos searchtrack "fixing hair"` works
- **Workaround**: Try alternative search terms if a search fails unexpectedly
- **Status**: Documented in `SEARCH_API_ISSUE.md` for future SoCo library fix

This is a known issue with the underlying SoCo library's parsing of Amazon Music API responses, not with our enhanced search system.