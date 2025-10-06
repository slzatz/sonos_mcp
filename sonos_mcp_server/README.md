# Sonos MCP Server

A standalone Model Context Protocol (MCP) server for controlling Sonos speakers. This server exposes 17 tools for natural language control of Sonos systems.

## Architecture

This is a **standalone MCP server** that runs as a separate process and communicates via stdio transport. It can be used by:
- Claude Agent SDK applications
- Claude Desktop
- Any other MCP-compatible client

### Key Differences from In-Process Tools

**Previous Architecture (In-Process):**
```
Agent → create_sdk_mcp_server() → @tool functions → sonos_actions
(Everything in same Python process)
```

**New Architecture (Standalone Server):**
```
sonos_mcp_server/server.py (separate process)
    ↓ stdio transport (JSON-RPC)
Agent/Client (connects via MCP protocol)
```

**Benefits:**
- ✅ True client/server separation
- ✅ Can be used by multiple MCP clients (Claude Desktop, custom agents, etc.)
- ✅ Can be long-running to reduce startup overhead
- ✅ Better isolation and error handling
- ✅ Follows MCP specification exactly

## Installation

### 1. Install Dependencies

```bash
cd sonos_mcp_server
pip install -r requirements.txt
```

Note: The server also requires the parent `sonos` module dependencies (soco, etc.) which are defined in the parent project's `pyproject.toml`.

### 2. Configure Master Speaker

The server uses the master speaker setting from `../sonos/config.py`. Make sure `master_speaker` is configured correctly:

```python
# In sonos/config.py
master_speaker = "Your Speaker Name"
```

## Running the Server

### Manual Start (Recommended for Development)

```bash
# From the sonos_mcp_server directory
python3 server.py

# Or make it executable and run directly
chmod +x server.py
./server.py
```

The server will:
1. Initialize connection to the master speaker (with retry logic)
2. Start listening on stdio for MCP protocol messages
3. Log connection status to stderr

### Auto-Launch via Agent

The Claude SDK Agent (`claude_sdk_agent/sdk_agent.py`) is configured to auto-launch the server when needed. No manual start required.

## Available Tools (17 total)

### Speaker Management (2 tools)
- `get_master_speaker` - Get current master speaker name
- `set_master_speaker` - Change to a different Sonos speaker

### Music Search (2 tools)
- `search_for_track` - Search for tracks by title/artist
- `search_for_album` - Search for albums by title/artist

### Queue Management (5 tools)
- `add_track_to_queue` - Add track from search results
- `add_album_to_queue` - Add album from search results
- `list_queue` - Display current queue
- `clear_queue` - Clear all tracks
- `play_from_queue` - Play specific track from queue

### Playback Control (3 tools)
- `current_track` - Get currently playing track info
- `play_pause` - Toggle play/pause
- `next_track` - Skip to next track

### Playlist Management (5 tools)
- `add_to_playlist_from_queue` - Add track from queue to playlist
- `add_to_playlist_from_search` - Add track from search to playlist
- `add_playlist_to_queue` - Add entire playlist to queue
- `list_playlist_tracks` - Show all tracks in a playlist
- `remove_track_from_playlist` - Remove track from playlist

## Configuration for Different Clients

### 1. Claude Agent SDK (Python)

The `claude_sdk_agent/sdk_agent.py` is already configured:

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

options = ClaudeAgentOptions(
    mcp_servers={
        "sonos": {
            "command": "python3",
            "args": ["/absolute/path/to/sonos_mcp_server/server.py"]
        }
    },
    allowed_tools=["mcp__sonos__*"]  # All sonos tools
)

client = ClaudeSDKClient(options=options)
```

### 2. Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sonos": {
      "command": "python3",
      "args": ["/absolute/path/to/sonos_mcp_server/server.py"]
    }
  }
}
```

Then restart Claude Desktop. The Sonos tools will appear in the tool selector.

### 3. MCP Inspector (Testing)

Use the MCP Inspector to test the server:

```bash
npx @modelcontextprotocol/inspector python3 /absolute/path/to/sonos_mcp_server/server.py
```

This provides a web UI for testing all tools.

## Usage Examples

### With Claude Agent SDK

```bash
cd claude_sdk_agent
python3 sdk_agent.py
```

Then interact naturally:
- "Play some Neil Young"
- "What's currently playing?"
- "Add track 3 to my favorites playlist"
- "Switch to the bedroom speaker"

### With Claude Desktop

After configuration, just chat with Claude:
- "Show me what's in the queue"
- "Search for Harvest Moon by Neil Young"
- "Add album 1 to the queue and play it"

## Architecture Details

### FastMCP Framework

The server uses **FastMCP** from the MCP Python SDK, which provides:
- Automatic tool registration via `@mcp.tool()` decorator
- Type hint-based input validation
- Simplified response formatting
- Built-in stdio transport support

### Tool Definition Example

```python
@mcp.tool()
async def search_for_track(query: str) -> str:
    """
    Search for music tracks by title, artist, or both.

    Args:
        query: Search query (e.g., "Heart of Gold Neil Young")
    """
    try:
        result = sonos_actions.search_for_track(query)
        return result
    except Exception as e:
        return f"Failed to search for track: {str(e)}"
```

FastMCP automatically:
1. Generates MCP tool schema from function signature and docstring
2. Validates input parameters
3. Formats string return value as MCP text content
4. Handles async execution

### Speaker Initialization

The server initializes the Sonos speaker connection on startup with retry logic:
- Up to 10 connection attempts
- 1-second delay between attempts
- Logs all attempts to stderr
- Graceful error handling if speaker unavailable

### Logging

All logging goes to **stderr** (required for stdio transport):
- Speaker connection status
- Tool execution (in verbose mode)
- Errors and warnings

Never writes to stdout (would corrupt MCP protocol).

## Troubleshooting

### Server won't start

**Check speaker connection:**
```bash
# Run server manually to see connection attempts
python3 server.py
```

**Verify master speaker name:**
```python
# In sonos/config.py
master_speaker = "Exact Speaker Name"  # Case-sensitive
```

### Agent can't connect to server

**Check server path:**
```python
# Make sure path is absolute
server_path = "/full/absolute/path/to/sonos_mcp_server/server.py"
```

**Test with MCP Inspector:**
```bash
npx @modelcontextprotocol/inspector python3 /path/to/server.py
```

### Tools not appearing

**Check allowed_tools list:**
```python
allowed_tools=[
    "mcp__sonos__search_for_track",  # Must include mcp__sonos__ prefix
    "mcp__sonos__play_from_queue",
    # ... etc
]
```

### Speaker discovery failing

**Common causes:**
- Speaker name doesn't match exactly
- Speaker is off or not on network
- Network connectivity issues
- SoCo discovery timeout

**Fix:**
```python
# Increase retry attempts in server.py
sonos_actions.master = initialize_speaker(max_retries=20)
```

## Development

### Adding New Tools

1. Add the function to `sonos/sonos_actions.py`
2. Add MCP tool wrapper in `server.py`:

```python
@mcp.tool()
async def your_new_tool(param: str) -> str:
    """Tool description for Claude."""
    try:
        result = sonos_actions.your_new_function(param)
        return result
    except Exception as e:
        return f"Error: {str(e)}"
```

3. Add to `allowed_tools` in `claude_sdk_agent/sdk_agent.py`:

```python
allowed_tools=[
    # ... existing tools
    "mcp__sonos__your_new_tool"
]
```

### Testing

**Test server directly:**
```bash
# Start server
python3 server.py

# Should see:
# Starting Sonos MCP Server...
# Successfully connected to speaker: YourSpeaker
```

**Test with MCP Inspector:**
```bash
npx @modelcontextprotocol/inspector python3 server.py
# Opens web UI at http://localhost:5173
```

**Test with agent:**
```bash
cd claude_sdk_agent
python3 sdk_agent.py -v  # Verbose mode shows tool calls
```

## Migration from In-Process Tools

If migrating from the old `sonos_mcp_tools.py` approach:

1. ✅ New standalone server is already created
2. ✅ Agent is already updated to use external server
3. ✅ Old `sonos_mcp_tools.py` has been removed
4. ⚠️ Update any other agents/clients to use new server config

## Related Documentation

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP Documentation](https://docs.modelcontextprotocol.io/docs/tools/fastmcp)
- [Claude Agent SDK](https://docs.anthropic.com/en/api/agent-sdk)
- [SoCo Library](https://github.com/SoCo/SoCo)

## License

Same as parent project.
