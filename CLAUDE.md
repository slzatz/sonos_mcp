# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A comprehensive Sonos speaker control system with natural language interface using Claude AI. The project provides both programmatic Python APIs and an AI-powered conversational agent for controlling Sonos speakers through the Model Context Protocol (MCP).

**Key Features:**
- Natural language control: "Play Heart of Gold by Neil Young"
- Music search across Amazon Music
- Queue and playlist management
- Multi-speaker support with dynamic speaker switching
- Session resumption for continuous conversations
- MCP server compatible with Claude Desktop and other MCP clients

## Architecture

The project uses a **standalone MCP server architecture**:

```
User/Client
    ↓
Claude Agent SDK (claude_sdk_agent/)
    ↓ MCP Protocol (stdio transport)
Sonos MCP Server (sonos_mcp_server/)
    ↓ Direct Python imports
Sonos Actions Library (sonos/)
    ↓ SoCo Library
Sonos Speakers (network)
```

**Key Design Principles:**
1. **Separation of Concerns**: MCP server runs as independent process
2. **Reusability**: Server works with any MCP-compatible client
3. **Direct Execution**: No subprocess overhead, direct Python function calls
4. **Standard Protocol**: Follows official MCP specification

## Project Structure

```
sonos_mcp/
├── sonos/                      # Core Sonos control library
│   ├── __init__.py
│   ├── sonos_actions.py        # Main Sonos operations using SoCo
│   ├── config.py               # User configuration (speaker, API keys)
│   ├── sonos_config.py         # DIDL templates and metadata formats
│   ├── get_lyrics.py           # Genius API integration for lyrics
│   └── cli.py                  # Legacy CLI (not used by agent)
│
├── sonos_mcp_server/           # Standalone MCP Server
│   ├── server.py               # FastMCP server with 17 tools
│   ├── requirements.txt        # MCP SDK dependencies
│   ├── __init__.py
│   └── README.md               # Server documentation
│
├── claude_sdk_agent/           # Claude Agent SDK Client
│   ├── sdk_agent.py            # Interactive agent (connects to MCP server)
│   ├── system_prompt.py        # Music domain system prompt
│   ├── requirements.txt        # Agent dependencies
│   └── .env                    # ANTHROPIC_API_KEY (gitignored)
│
├── pyproject.toml              # Project dependencies and metadata
├── CLAUDE.md                   # This file
├── IMPLEMENTATION_SUMMARY.md   # Technical implementation details
└── README.md                   # User-facing documentation
```

## Core Components

### 1. Sonos Library (`sonos/`)

**Purpose**: Core Python library for Sonos speaker control using the SoCo package.

**Key Files:**
- **`sonos_actions.py`**: Main implementation of Sonos operations
  - Music search (tracks, albums)
  - Queue management (add, remove, play, clear)
  - Playback control (play/pause, next, current track)
  - Playlist management (load, save, edit)
  - Speaker management (get/set master speaker)

- **`config.py`**: User configuration (gitignored, user-created)
  ```python
  master_speaker = "Office2"        # Default Sonos speaker name
  music_service = "Amazon Music"    # Music service name
  api_url = "https://genius.com/api" # Genius API for lyrics
  ```

- **`sonos_config.py`**: Sonos metadata templates
  - DIDL (Digital Item Declaration Language) templates
  - Metadata formats for tracks, albums, playlists
  - Radio station definitions

**Dependencies:**
- `soco`: Python library for Sonos speaker control
- `httpx`: HTTP client for API requests
- `unidecode`: Unicode text normalization

### 2. MCP Server (`sonos_mcp_server/`)

**Purpose**: Standalone MCP server exposing Sonos functionality as MCP tools.

**Architecture:**
- Built with **FastMCP** framework
- Uses **stdio transport** for local communication
- Runs as separate process (launched by agent)
- Auto-exits when client disconnects

**Available Tools (17 total):**

*Speaker Management (2 tools):*
- `get_master_speaker` - Get current master speaker name
- `set_master_speaker` - Switch to different speaker

*Music Search (2 tools):*
- `search_for_track` - Search tracks by title/artist
- `search_for_album` - Search albums by title/artist

*Queue Management (5 tools):*
- `add_track_to_queue` - Add track from search results
- `add_album_to_queue` - Add album from search results
- `list_queue` - Display current queue
- `clear_queue` - Clear all tracks
- `play_from_queue` - Play specific track by position

*Playback Control (3 tools):*
- `current_track` - Get currently playing track info
- `play_pause` - Toggle play/pause
- `next_track` - Skip to next track

*Playlist Management (5 tools):*
- `add_to_playlist_from_queue` - Add track from queue to playlist
- `add_to_playlist_from_search` - Add track from search to playlist
- `add_playlist_to_queue` - Load entire playlist to queue
- `list_playlist_tracks` - Show all tracks in playlist
- `remove_track_from_playlist` - Remove track from playlist

**Server Initialization:**
- Connects to master speaker with retry logic (up to 10 attempts)
- Loads configuration from `sonos/config.py`
- Logs to stderr (stdio-safe for MCP protocol)
- Graceful error handling for all operations

### 3. Claude Agent (`claude_sdk_agent/`)

**Purpose**: Interactive conversational agent using Claude Agent SDK.

**Features:**
- Natural language music control
- Session resumption (`-r SESSION_ID` or `-c` for continue)
- Verbose mode (`-v`) to show tool calls
- Conversation logging (`-l LOG_FILE`)
- Auto-launches MCP server on startup

**Model**: Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`)

**Key Components:**
- **`sdk_agent.py`**: Main agent application
  - `SonosSDKAgent` class manages agent lifecycle
  - Connects to external MCP server via stdio
  - Handles conversation flow and tool execution
  - Session management and logging

- **`system_prompt.py`**: Comprehensive music domain prompt
  - Guides Claude on Sonos operations
  - Explains tool usage workflows
  - Provides examples for common tasks

## Setup and Installation

### Prerequisites
- Python 3.10 or higher
- Sonos speaker on local network
- Anthropic API key
- Amazon Music account (configured with Sonos)

### Installation Steps

1. **Install dependencies:**
   ```bash
   # Install project dependencies
   uv sync

   # Or using pip
   pip install -e .
   ```

2. **Configure Sonos:**
   Create `sonos/config.py`:
   ```python
   master_speaker = "Your Speaker Name"  # Exact speaker name
   music_service = "Amazon Music"
   api_url = "https://genius.com/api"
   ```

3. **Set API key:**
   Create `claude_sdk_agent/.env`:
   ```
   ANTHROPIC_API_KEY=your-api-key-here
   ```

4. **Verify speaker connection:**
   ```bash
   # Test server startup
   .venv/bin/python3 sonos_mcp_server/server.py
   # Should see: "Successfully connected to speaker: YourSpeaker"
   # Press Ctrl+C to stop
   ```

## Usage

### Running the Agent

```bash
cd claude_sdk_agent

# Basic usage
python3 sdk_agent.py

# With verbose mode (shows tool calls)
python3 sdk_agent.py -v

# With logging
python3 sdk_agent.py -l session.log

# Resume a specific session
python3 sdk_agent.py -r abc123def456

# Continue most recent conversation
python3 sdk_agent.py -c

# Combine options
python3 sdk_agent.py -v -l debug.log
```

### Example Conversations

**Basic playback:**
```
🎵 You: Play Heart of Gold by Neil Young
🔧 [TOOL] search_for_track(query='Heart of Gold by Neil Young')
🔧 [TOOL] add_track_to_queue(position=1)
🔧 [TOOL] play_from_queue(position=1)
🤖 Assistant: Now playing "Heart of Gold" by Neil Young!
```

**Queue management:**
```
🎵 You: What's in the queue?
🔧 [TOOL] list_queue()
🤖 Assistant: Your queue has 5 tracks:
1. Heart of Gold - Neil Young - Harvest
2. Old Man - Neil Young - Harvest
3. ...
```

**Playlist operations:**
```
🎵 You: Add track 2 from the queue to my favorites playlist
🔧 [TOOL] add_to_playlist_from_queue(playlist='favorites', position=2)
🤖 Assistant: Added "Old Man" by Neil Young to your favorites playlist!
```

**Speaker management:**
```
🎵 You: What's the current speaker?
🔧 [TOOL] get_master_speaker()
🤖 Assistant: The current master speaker is Office2.

🎵 You: Switch to the bedroom speaker
🔧 [TOOL] set_master_speaker(speaker_name='Bedroom')
🤖 Assistant: Successfully changed master speaker to Bedroom!
```

### Using with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sonos": {
      "command": "/full/path/to/.venv/bin/python3",
      "args": ["/full/path/to/sonos_mcp_server/server.py"]
    }
  }
}
```

Restart Claude Desktop. The Sonos tools will appear in the tool selector.

### Testing with MCP Inspector

```bash
npx @modelcontextprotocol/inspector \
  /full/path/to/.venv/bin/python3 \
  /full/path/to/sonos_mcp_server/server.py
```

Opens web UI at `http://localhost:5173` for testing tools.

## Development Guide

### Adding New Tools

1. **Add function to `sonos/sonos_actions.py`:**
   ```python
   def your_new_function(param: str) -> str:
       """Implementation of new functionality."""
       # Your code here
       return result
   ```

2. **Add MCP tool to `sonos_mcp_server/server.py`:**
   ```python
   @mcp.tool()
   async def your_new_tool(param: str) -> str:
       """Description shown to Claude."""
       try:
           result = sonos_actions.your_new_function(param)
           return result
       except Exception as e:
           return f"Error: {str(e)}"
   ```

3. **Register tool in `claude_sdk_agent/sdk_agent.py`:**
   ```python
   allowed_tools=[
       # ... existing tools
       "mcp__sonos__your_new_tool"
   ]
   ```

### Testing

**Test server startup:**
```bash
.venv/bin/python3 sonos_mcp_server/server.py
# Should connect to speaker and start server
```

**Test specific tool:**
```bash
# Create test script
cat > test_tool.py << 'EOF'
from sonos import sonos_actions
result = sonos_actions.your_function()
print(result)
EOF

python3 test_tool.py
```

**Test agent integration:**
```bash
python3 claude_sdk_agent/sdk_agent.py -v
# Ask Claude to use the new tool
```

### Code Organization

**Follow these patterns:**

1. **Pure Python functions** in `sonos/sonos_actions.py`:
   - No async unless necessary
   - Return simple types (str, dict, list)
   - Handle errors with try/except
   - Log to stderr, never stdout

2. **MCP tool wrappers** in `sonos_mcp_server/server.py`:
   - Always async (MCP requirement)
   - Simple parameter types (str, int, float, bool)
   - Return string descriptions for Claude
   - Format errors as user-friendly messages

3. **Agent configuration** in `claude_sdk_agent/sdk_agent.py`:
   - MCP server connection via stdio
   - Tool allowlist with `mcp__sonos__` prefix
   - System prompt for domain knowledge

## Configuration Files

### `sonos/config.py` (User-created, gitignored)

```python
# Master Speaker Configuration
master_speaker = "Speaker Name"  # Case-sensitive, exact match

# Music Service
music_service = "Amazon Music"

# Genius API (optional, for lyrics)
api_url = "https://genius.com/api"
api_key = None  # Set if you want lyrics support
```

### `sonos/sonos_config.py` (In repository)

Contains DIDL metadata templates and constants:
- `STATIONS`: Radio station definitions
- `META_FORMAT_*`: Metadata format templates
- `DIDL_*`: Digital Item Declaration Language templates
- `SONOS_DIDL`: Main DIDL template for tracks/albums

### `.env` (User-created, gitignored)

```bash
ANTHROPIC_API_KEY=sk-ant-...
```

## Key Features

### Session Resumption

The agent supports resuming previous conversations:

```bash
# Agent prints session ID on exit:
# Session ID: abc123def456

# Resume that specific session:
python3 sdk_agent.py -r abc123def456

# Or continue most recent:
python3 sdk_agent.py -c
```

Session data stored by Claude Code CLI, includes full conversation history.

### Playlist Management

Playlists stored as JSON in `~/.sonos/playlists/`:

```json
[
  {
    "title": "Heart of Gold",
    "artist": "Neil Young",
    "album": "Harvest",
    "item_id": "catalog/tracks/B001...",
    "uri": "soco://0fffffff..."
  }
]
```

Operations:
- Create: Add first track to new playlist name
- View: `list_playlist_tracks`
- Edit: `add_to_playlist_*`, `remove_track_from_playlist`
- Play: `add_playlist_to_queue`

### Speaker Discovery

The MCP server uses SoCo speaker discovery with retry logic:

```python
# Attempts up to 10 times with 1-second delays
# Logs each attempt to stderr
# Gracefully handles speaker unavailability
```

If speaker connection fails:
- Server still starts (tools will return errors)
- Retry on first tool call
- Clear error messages to user

### Verbose Mode

Shows tool execution in real-time:

```
🎵 You: play neil young
🔧 [TOOL] search_for_track(query='neil young')
🔧 [TOOL] add_track_to_queue(position=1)
🔧 [TOOL] play_from_queue(position=1)
🤖 Assistant: Playing Neil Young!
```

Essential for:
- Debugging tool calls
- Understanding agent behavior
- Verifying correct tool usage
- Development and testing

## Music Service Integration

The project integrates with Amazon Music (configurable) using the SoCo library:
- **Search**: Full-text search across tracks and albums
- **Metadata**: DIDL format for Sonos compatibility
- **Playback**: Direct queue manipulation
- **Authentication**: Handled by Sonos system (one-time setup)

**Other services** (Spotify, Pandora, etc.) can be configured via `sonos/config.py` and `sonos_config.py` with appropriate DIDL templates.

## Troubleshooting

### MCP Server Won't Start

**Check speaker connection:**
```bash
.venv/bin/python3 sonos_mcp_server/server.py
# Look for: "Successfully connected to speaker: YourSpeaker"
```

**Verify config:**
- `sonos/config.py` exists with correct speaker name
- Speaker name matches exactly (case-sensitive)
- Speaker is powered on and on network

### Agent Can't Find Tools

**Verify venv path:**
```bash
# In sdk_agent.py, check:
venv_python = project_root / ".venv" / "bin" / "python3"
# Should match your actual venv location
```

**Check MCP server logs:**
```bash
# Run agent in verbose mode
python3 sdk_agent.py -v
# Look for server startup messages
```

### Authentication Errors

If Amazon Music auth expires:
1. Open Sonos app
2. Go to Settings → Services
3. Re-authorize Amazon Music
4. Restart MCP server

### Speaker Discovery Fails

```bash
# Test SoCo discovery directly:
python3 -c "
import soco
speakers = soco.discover()
print([s.player_name for s in speakers])
"
```

Should show all Sonos speakers on network.

## References

- **MCP Protocol**: https://modelcontextprotocol.io/
- **Claude Agent SDK**: https://docs.anthropic.com/en/api/agent-sdk
- **SoCo Library**: https://github.com/SoCo/SoCo
- **FastMCP**: https://docs.modelcontextprotocol.io/docs/tools/fastmcp
- **Anthropic API**: https://docs.anthropic.com/

## Project Status

**Production Ready**: The MCP server architecture is fully implemented, tested, and ready for use with:
- Claude Agent SDK (current implementation)
- Claude Desktop (configuration provided)
- MCP Inspector (for testing)
- Any MCP-compatible client

All 17 tools are functional and tested end-to-end.
