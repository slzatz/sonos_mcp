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

The application integrates with Amazon Music as the primary music service (configured in config.py) using the SoCo python package: https://github.com/SoCo/SoCo.

## Key Functions
The main Sonos actions are implemented in `sonos_actions.py` and include:
- **search_track()**: Search for tracks by title and artist and bring back a list of results
- **search_album()**: Search for albums by title and artist
- **select_from_list()**: Select a track or album from the lists produced by search_track or search_album
- **play_from_queue()**: Play a selected track or album from the Sonos queue
- **current_track_info()**: Get information about currently playing track

Note that these functions are called by the CLI commands defined in `cli.py` and the correspondence between CLI command and sonos_actions functions is straightforward.  For example, the cli command `sonos searchtrack` calls `sonos_actions.search_track()` and the cli command `sonos playfromqueue` calls `sonos_actions.play_from_queue()`.

## Sonos Claude Agents

Natural language interfaces for controlling Sonos speakers using Claude AI. Two implementations are available:

### 1. Original Agent (sonos_agent/)
Standard implementation using the Anthropic Python SDK directly.

**Location:**
- **sonos_agent/**: Original agent implementation
  - **sonos_agent.py**: Main interactive agent application (383 lines)
  - **sonos_tools.py**: CLI wrapper functions for Claude tools
  - **system_prompt.py**: Music domain system prompt for Claude
  - **test_tools.py**: Tool functionality verification script
  - **requirements.txt**: Dependencies (anthropic SDK)
  - **README.md**: Detailed agent documentation

**Model:** Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`)

### 2. Claude Agent SDK Implementation (claude_sdk_agent/)
Production-ready rewrite using the official Claude Agent SDK with direct Python function calls for optimal performance.

**Location:**
- **claude_sdk_agent/**: SDK-based agent implementation
  - **sdk_agent.py**: Main agent using ClaudeSDKClient (265 lines)
  - **sonos_mcp_tools.py**: MCP tools using direct Python imports (no subprocess overhead)
  - **system_prompt.py**: Comprehensive music domain prompt with workflow examples
  - **requirements.txt**: Dependencies (claude-agent-sdk)
  - **README.md**: SDK-specific documentation
  - **USAGE.md**: Quick start guide
  - **REFACTORING_PLAN.md**: Documentation of CLI-to-direct-call refactoring

**Model:** Claude Sonnet 4.5 (uses Claude Code CLI default)

**Key Advantages:**
- **~100x faster performance**: Direct Python function calls instead of subprocess CLI wrappers
- **30% less code**: 265 vs 383 lines in main agent
- **Session resumption**: Resume by ID (`-r SESSION_ID`) or continue most recent (`-c`)
- **Robust initialization**: Retry logic for flaky SoCo speaker discovery (up to 10 attempts)
- **Playlist management**: View and edit saved playlists with dedicated tools
- **Automatic conversation management**: Via ClaudeSDKClient
- **Cleaner tool definitions**: Using `@tool` decorator and MCP server architecture

**Available Tools (15 total):**
- Search: `search_for_track`, `search_for_album`
- Queue Management: `add_track_to_queue`, `add_album_to_queue`, `list_queue`, `clear_queue`, `play_from_queue`
- Playlist Management: `add_to_playlist_from_queue`, `add_to_playlist_from_search`, `add_playlist_to_queue`, `list_playlist_tracks`, `remove_track_from_playlist`
- Playback Control: `current_track`, `play_pause`, `next_track`

**Usage:**
```bash
cd claude_sdk_agent

# Basic usage
python3 sdk_agent.py

# Resume a specific session
python3 sdk_agent.py -r abc123def456

# Continue most recent session
python3 sdk_agent.py -c

# With verbose mode and logging
python3 sdk_agent.py -v -l session.log
```

### Common Features (Both Agents)

Both agents provide natural language control over Sonos through conversational commands:
- "Play some Neil Young" → searches and plays music
- "What's currently playing?" → shows track information
- "Show me the queue" → displays current music queue
- "Skip to the next song" → controls playback

**SDK Agent Additional Features:**
- "What's in my favorites playlist?" → shows all tracks in saved playlist
- "Remove track 5 from favorites" → removes specific track from playlist
- "Add the current track to my workout playlist" → adds track to playlist from queue
- Playlists stored as JSON in `~/.sonos/playlists/<playlist_name>`

### Architecture

**Original Agent:**
```
User Input → Claude Agent → Tool Selection → Sonos CLI (subprocess) → Sonos Speakers
```

**SDK Agent (Refactored):**
```
User Input → Claude Agent → Tool Selection → sonos_actions.py (direct import) → Sonos Speakers
```

Key architectural differences:
- **Original**: Uses subprocess calls to `sonos` CLI commands (slower but isolated)
- **SDK Agent**: Direct Python imports from `sonos.sonos_actions` (~100x faster, shared state)
- Both use Claude's function calling to execute appropriate Sonos operations
- Both maintain conversation context for multi-step music workflows
- Both handle search, selection, playback, queue management, and playlists

### Setup

**Original Agent:**
1. Install dependencies: `pip install -r sonos_agent/requirements.txt`
2. Set API key: `export ANTHROPIC_API_KEY='your-key'`
3. Run: `cd sonos_agent && python3 sonos_agent.py`
4. Optional flags: `-v` (verbose), `-l` (logging)

**SDK Agent:**
1. Install Claude Code CLI: `npm install -g @anthropic-ai/claude-code`
2. Install dependencies: `pip install -r claude_sdk_agent/requirements.txt`
3. Set API key: `export ANTHROPIC_API_KEY='your-key'`
4. Run: `cd claude_sdk_agent && python3 sdk_agent.py`
5. Optional flags: `-v` (verbose), `-l` (logging), `-r SESSION_ID` (resume), `-c` (continue)

Both require working Sonos CLI setup and valid Anthropic API key.

### Verbose Mode
The agent supports a verbose mode that shows tool calls and results during conversations:

**Normal mode:**
```
🎵 You: Play some Neil Young
🤖 Assistant: I found several Neil Young songs. Which would you like?
```

**Verbose mode (`-v` flag):**
```
🎵 You: Play some Neil Young
🔧 [TOOL] search_track(query='neil young')
📋 [RESULT] Found 15 results: Heart of Gold, Old Man, Harvest Moon...
🤖 Assistant: I found several Neil Young songs. Which would you like?
```

Verbose mode provides transparency into:
- Which tools the agent calls and with what parameters
- Summarized results from tool execution (search counts, track info, etc.)
- Multi-step tool workflows (search → select → play sequences)
- Error messages from failed tool calls

### Enhanced Workflow Behavior
The agent now follows an optimized workflow for playing specific tracks:

**When you request a specific track** (e.g., "play Like a Hurricane by Neil Young"):
1. **Search**: Finds matching tracks using `search_track`
2. **Select**: Automatically selects the best match and adds to queue using `select_from_list`
3. **Locate**: Uses `show_queue` to find where the track was added
4. **Play**: Immediately starts playing from that position using `play_from_queue`
5. **Confirm**: Reports what's now playing

**Example with verbose mode:**
```
🎵 You: play like a hurricane by neil young
🔧 [TOOL] search_track(query='like a hurricane neil young')
📋 [RESULT] Found 25 results: Like a Hurricane (2003 Remaster), Like a Hurricane (Unplugged)...
🔧 [TOOL] select_from_list(position=9)
🔧 [TOOL] show_queue()
📋 [RESULT] Queue contains 49 tracks
🔧 [TOOL] play_from_queue(position=49)
📋 [RESULT] 'Like a Hurricane' by Neil Young
🤖 Assistant: Now playing "Like a Hurricane" by Neil Young!
```

The agent automatically executes this complete workflow without asking for permission, providing a seamless music experience.


