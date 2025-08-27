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

Claude Code now has TWO approaches for handling music requests: an intelligent agent-based approach for natural language requests, and the traditional CLI approach for manual control.

### Automatic Music Request Detection

**When Claude Code detects any of these natural language patterns, automatically use the music agent:**

#### Natural Language Patterns
- **Direct requests**: "play [song/artist]", "I'd like to hear...", "Can you play...", "Put on..."
- **Artist possessive forms**: "Neil Young's Harvest", "Ani DiFranco's fixing her hair", "The Beatles' Here Comes the Sun"  
- **Preference requests**: "live version of...", "acoustic version of...", "studio version of..."
- **Casual requests**: "some [artist]", "something by [artist]", "[song] by [artist]"

#### Auto-Detection Examples
✅ **These should automatically trigger the music agent:**
- "I'd like to hear a live version of Neil Young's Harvest"
- "Play some Beatles"  
- "Put on Ani DiFranco's fixing her hair"
- "Can you play Harvest by Neil Young?"
- "I want to hear something by Pink Floyd"
- "Play a live version of Comfortably Numb"

### Primary Method: Intelligent Music Agent (Recommended)

For any detected music request, automatically use the intelligent agent:

```python
from claude_music_interface import play_music

# Single-step intelligent workflow
result = play_music(user_request)
print(result)  # "Now playing: [Track] by [Artist]"
```

#### Agent Capabilities
- **Natural Language Understanding**: Handles possessives, complex grammar, preferences
- **Smart Search Strategy**: Multiple query variations with fallback strategies  
- **API Error Recovery**: Automatically handles known Amazon Music API parsing issues
- **Contextual Selection**: Uses reasoning to select best match from results
- **Live Version Detection**: Intelligently finds live/acoustic/studio versions when requested

#### Agent Examples
```python
# These all work automatically:
play_music("I'd like to hear a live version of Neil Young's Harvest")
play_music("Ani DiFranco's fixing her hair")  # Handles possessives perfectly
play_music("something by The Beatles")
play_music("play Comfortably Numb by Pink Floyd")
```

The agent handles the entire workflow internally - no need for separate search and selection steps.

### Fallback Method: Manual CLI Workflow (Advanced Users)

When you need manual control or the agent approach fails, use the traditional two-step process:

#### 1. Search for Tracks
```bash
sonos searchtrack harvest by neil young
```

Returns numbered results:
```
1. Harvest Moon-Neil Young-Harvest Moon
2. Harvest (2009 Remaster)-Neil Young-Harvest (2009 Remaster)  
3. Heart of Gold-Neil Young-Harvest
4. Harvest-Neil Young-Harvest
5. Harvest (Live)-Neil Young & Stray Gators-Tuscaloosa (Live)
```

#### 2. Select and Play
```bash
sonos playtrackfromlist 4
```

#### When to Use Manual CLI
- **Advanced Control**: When you want to see all search results before selecting
- **Agent Fails**: If the intelligent agent can't find what you want
- **Debugging**: When you need to understand why a search behaved a certain way
- **Scripting**: When building automated workflows

### Additional Sonos Commands

**Playback Control:**
- `sonos what` - Current track info
- `sonos pause` / `sonos resume` - Pause/resume playback  
- `sonos louder` / `sonos quieter` - Volume control
- `sonos showqueue` - View playback queue

**Alternative Interface Functions:**
```python  
from claude_music_interface import pause_music, resume_music, get_current_track

pause_music()     # Pause playback
resume_music()    # Resume playback  
get_current_track()  # Get current track info
```

## Decision Tree for Claude Code

**Use this decision tree to determine how to handle user requests:**

```
User Request → Contains music patterns? 
                ↓
              YES → Use Agent: play_music(request)
                ↓
              NO → Regular sonos CLI command or other action
```

### Music Request Detection Patterns

**Automatically trigger the music agent when user input contains:**

#### High-Confidence Patterns (Definite music requests)
- **Command verbs**: "play", "put on", "start", "queue up"
- **Request phrases**: "I'd like to hear", "Can you play", "I want to listen to" 
- **Possessive forms**: "[Artist]'s [Song]" (e.g., "Neil Young's Harvest")
- **By constructions**: "[Song] by [Artist]" (e.g., "Harvest by Neil Young")

#### Medium-Confidence Patterns (Likely music requests)  
- **Preference requests**: "live version of", "acoustic version", "studio version"
- **Casual requests**: "some [artist]", "something by [artist]"
- **Artist mentions**: Names of known musicians in context

#### Pattern Examples with Expected Actions
```
✅ "I'd like to hear a live version of Neil Young's Harvest" 
   → play_music("I'd like to hear a live version of Neil Young's Harvest")

✅ "Play some Beatles" 
   → play_music("Play some Beatles")

✅ "Put on Ani DiFranco's fixing her hair"
   → play_music("Put on Ani DiFranco's fixing her hair")

✅ "Can you play Harvest by Neil Young?"
   → play_music("Can you play Harvest by Neil Young?")

❌ "What's the current track?"
   → get_current_track() or sonos what

❌ "Pause the music"  
   → pause_music() or sonos pause

❌ "Make it louder"
   → sonos louder
```

## Legacy Helper Functions (Deprecated)

The `sonos_helpers.py` module is now deprecated in favor of the intelligent agent, but remains available for reference:

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