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

## Sonos Claude Agent

A natural language interface for controlling Sonos speakers using the Anthropic Claude SDK. This agent wraps the existing Sonos CLI commands to provide conversational music control.

### Location
- **sonos_agent/**: Claude agent implementation directory
  - **sonos_agent.py**: Main interactive agent application
  - **sonos_tools.py**: CLI wrapper functions for Claude tools
  - **system_prompt.py**: Music domain system prompt for Claude
  - **test_tools.py**: Tool functionality verification script
  - **requirements.txt**: Claude SDK dependencies
  - **README.md**: Detailed agent documentation

### Usage
The agent provides natural language control over Sonos through conversational commands:
- "Play some Neil Young" → searches and plays music
- "What's currently playing?" → shows track information
- "Show me the queue" → displays current music queue
- "Skip to the next song" → controls playback

### Architecture
```
User Input → Claude Agent → Tool Selection → Sonos CLI → Sonos Speakers
```
- Uses Claude's function calling to execute appropriate Sonos CLI commands
- Maintains conversation context for multi-step music workflows
- Handles search, selection, playback, and queue management

### Setup
1. Install dependencies: `pip install -r sonos_agent/requirements.txt`
2. Set API key: `export ANTHROPIC_API_KEY='your-key'`
3. Run agent: `cd sonos_agent && python3 sonos_agent.py`
4. Optional: Use verbose mode: `python3 sonos_agent.py -v` or `python3 sonos_agent.py --verbose`

Requires working Sonos CLI setup and valid Anthropic API key.

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


