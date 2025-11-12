# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A comprehensive Sonos speaker control system with natural language interface using Claude AI. The project provides both programmatic Python APIs and an AI-powered conversational agent for controlling Sonos speakers through the Model Context Protocol (MCP).

**Key Features:**
- Natural language control: "Play Heart of Gold by Neil Young", "Turn it up", "Show my playlists"
- **Dual execution modes**: MCP server (portable) or direct Python (efficient)
- **Agent Skills architecture** with progressive disclosure for efficient context usage
- Music search across Amazon Music
- Queue and playlist management
- Volume control (adjust, set level, mute/unmute)
- Multi-speaker support with dynamic speaker switching
- Session resumption for continuous conversations
- Headless mode for one-off commands and scripting
- MCP server compatible with Claude Desktop and other MCP clients
- Modular skill updates without agent code changes

## Architecture

The project supports **two execution modes** for maximum flexibility:

### MCP Mode (Portable)
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

**Use Cases:**
- Claude Desktop integration
- Multi-client scenarios
- When portability matters
- Standard tool-based workflows

**Context Overhead:** ~17% (~34k tokens for 21 MCP tool definitions)

### Direct Mode (Efficient - Default)
```
User/Client
    ↓
Claude Agent SDK (claude_sdk_agent/)
    ↓ Bash tool → Dispatcher Tool (sonos_tool.py)
    ↓ Direct Python imports
Sonos Actions Library (sonos/)
    ↓ SoCo Library
Sonos Speakers (network)
```

**Use Cases:**
- Local development and testing
- Complex workflows requiring multiple operations
- Performance-critical operations
- Batch operations

**Context Overhead:** ~2.5% (~5k tokens for skill metadata)
**Token Savings:** ~15% compared to MCP mode

### Switching Between Modes

```bash
# Direct mode (default) - no flag needed
python3 sdk_agent.py

# MCP mode (explicit)
python3 sdk_agent.py --mode mcp

# Both modes support all features
python3 sdk_agent.py --mode direct -v -l session.log
python3 sdk_agent.py --mode mcp -p "play music"
```

**Key Design Principles:**
1. **Dual Execution**: Choose between MCP (portable) or direct (efficient)
2. **Separation of Concerns**: MCP server runs as independent process when needed
3. **Reusability**: MCP server works with any MCP-compatible client
4. **Direct Efficiency**: Skip protocol overhead for local development
5. **Standard Protocol**: Follows official MCP specification
6. **Modular Knowledge**: Agent Skills provide domain expertise via progressive disclosure

## Project Structure

```
sonos_mcp/
├── .claude/                    # Agent Skills (auto-discovered)
│   └── skills/
│       ├── sonos-control/      # MCP mode: Sonos domain knowledge skill
│       │   ├── SKILL.md        # Main skill with workflows and tools
│       │   └── references/     # Additional reference materials
│       │       └── search_tips.md
│       └── sonos-direct-code/  # Direct mode: Dispatcher tool interface
│           ├── SKILL.md        # Tool documentation and workflows
│           └── sonos_tool.py   # CLI dispatcher (21 discrete tools)
│
├── sonos/                      # Core Sonos control library
│   ├── __init__.py
│   ├── sonos_actions.py        # Main Sonos operations using SoCo
│   ├── config.py               # User configuration (speaker, API keys)
│   ├── sonos_config.py         # DIDL templates and metadata formats
│   ├── get_lyrics.py           # Genius API integration for lyrics
│   └── cli.py                  # Legacy CLI (not used by agent)
│
├── sonos_mcp_server/           # Standalone MCP Server
│   ├── server.py               # FastMCP server with 21 tools
│   ├── requirements.txt        # MCP SDK dependencies
│   ├── __init__.py
│   └── README.md               # Server documentation
│
├── claude_sdk_agent/           # Claude Agent SDK Client
│   ├── sdk_agent.py            # Interactive agent (connects to MCP server)
│   ├── system_prompt.py        # Lightweight agent prompt (32 lines)
│   ├── requirements.txt        # Agent dependencies
│   └── .env                    # ANTHROPIC_API_KEY (gitignored)
│
├── pyproject.toml              # Project dependencies and metadata
├── CLAUDE.md                   # This file
├── IMPLEMENTATION_SUMMARY.md   # Technical implementation details
└── README.md                   # User-facing documentation
```

## Core Components

### 1. Agent Skills (`.claude/skills/`)

**Purpose**: Modular, filesystem-based domain knowledge that the Agent SDK auto-discovers.

**Architecture:**
- Skills follow Anthropic's Agent Skills specification
- Auto-discovered by Claude Agent SDK at runtime
- Implements **progressive disclosure**: metadata always loaded, detailed content loaded only when relevant
- Enables independent updates without modifying agent code
- Different skills for different execution modes

**Sonos Control Skill** (`.claude/skills/sonos-control/`) - Used in **MCP mode**:
- **`SKILL.md`**: Comprehensive MCP tool documentation
  - YAML frontmatter: name and description for auto-discovery
  - Tool descriptions: All 21 MCP tools with parameters
  - Workflows: Step-by-step guides (basic playback, custom mixes, playlists)
  - Advanced patterns: Live performances, multi-room control, error handling
  - Best practices: Selection logic, ambiguity resolution, natural responses
- **`references/`**: Additional reference materials
  - `search_tips.md`: Advanced search strategies and artist name variations

**Sonos Direct Code Skill** (`.claude/skills/sonos-direct-code/`) - Used in **Direct mode**:
- **`SKILL.md`**: Comprehensive dispatcher tool documentation
  - YAML frontmatter: name and description for auto-discovery
  - Tool descriptions: All 21 CLI tools with arguments and usage examples
  - Recommended tools: Current, working tools matching MCP functionality
  - Common workflows: Search/play, custom playlists, queue analysis
  - Execution patterns: CLI command structure and examples
  - Best practices: Error handling, two-step patterns, position indexing
- **`sonos_tool.py`**: Command-line dispatcher
  - 21 discrete tools matching MCP functionality
  - Automatic speaker initialization
  - Standardized error handling and output formatting
  - 1-indexed positions for user-friendly CLI experience

**Why Skills Over System Prompt:**
- **Modularity**: Update skill independently of agent code
- **Efficiency**: Progressive disclosure reduces context usage
- **Maintainability**: Skill changes don't require agent redeployment
- **Reusability**: Same skill works across claude.ai, Claude Desktop, and Agent SDK
- **Extensibility**: Add new skills without modifying agent architecture

**Discovery Process:**
1. Agent SDK scans `.claude/skills/` at startup
2. Loads skill metadata (name + description) into system prompt
3. When user request matches skill description, SDK reads SKILL.md
4. Skill content enters context window only when needed
5. Referenced files (like `references/search_tips.md`) loaded on demand

### 2. Sonos Library (`sonos/`)

**Purpose**: Core Python library for Sonos speaker control using the SoCo package.

**Key Files:**
- **`sonos_actions.py`**: Main implementation of Sonos operations
  - Music search (tracks, albums)
  - Queue management (add, remove, play, clear)
  - Playback control (play/pause, next, current track)
  - Playlist management (list, load, save, edit)
  - Speaker management (get/set master speaker)
  - Volume control (adjust, set level, mute/unmute)

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

### 3. MCP Server (`sonos_mcp_server/`)

**Purpose**: Standalone MCP server exposing Sonos functionality as MCP tools.

**Architecture:**
- Built with **FastMCP** framework
- Uses **stdio transport** for local communication
- Runs as separate process (launched by agent)
- Auto-exits when client disconnects

**Available Tools (21 total):**

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

*Volume Control (3 tools):*
- `turn_volume` - Adjust volume by 10 (louder/quieter)
- `set_volume` - Set absolute volume level (0-100)
- `mute` - Mute or unmute all speakers in group

*Playlist Management (8 tools):*
- `list_playlists` - Display all available local playlists
- `add_to_playlist_from_queue` - Add track from queue to local playlist
- `add_to_playlist_from_search` - Add track from search to local playlist
- `add_playlist_to_queue` - Load entire local playlist to queue (supports shuffle parameter for randomized playback)
- `list_playlist_tracks` - Show all tracks in local playlist
- `remove_track_from_playlist` - Remove track from local playlist
- `list_native_sonos_playlists` - Display all native Sonos playlists stored on Sonos system
- `create_native_sonos_playlist_from_local` - Convert local playlist to native Sonos playlist (accessible in Sonos app)

**Server Initialization:**
- Connects to master speaker with retry logic (up to 10 attempts)
- Loads configuration from `sonos/config.py`
- Logs to stderr (stdio-safe for MCP protocol)
- Graceful error handling for all operations

### 4. Claude Agent (`claude_sdk_agent/`)

**Purpose**: Interactive conversational agent using Claude Agent SDK with skill-based architecture.

**Features:**
- **Dual execution modes**: MCP server (portable) or direct Python (efficient)
- Natural language music control via auto-discovered skills
- Interactive and headless modes (`-p` for one-off commands)
- Session resumption (`-r SESSION_ID` or `-c` for continue)
- Verbose mode (`-v`) to show tool calls
- Conversation logging (`-l LOG_FILE`)
- Mode selection via `--mode` flag (default: direct)
- Automatic skill discovery from `.claude/skills/`

**Model**: Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`)

**Key Components:**
- **`sdk_agent.py`**: Main agent application
  - `SonosSDKAgent` class manages agent lifecycle
  - **MCP mode**: Connects to external MCP server via stdio
  - **Direct mode**: Uses Bash tool to call dispatcher (sonos_tool.py)
  - Handles conversation flow and tool execution
  - Session management and logging
  - No hardcoded skill references (skills auto-discovered)

- **`system_prompt.py`**: Lightweight agent personality
  - **`SONOS_SYSTEM_PROMPT`**: MCP mode prompt (references sonos-control skill)
  - **`SONOS_DIRECT_MODE_PROMPT`**: Direct mode prompt (references sonos-direct-code skill)
  - Agent role and behavioral guidelines
  - Core principles (proactive, knowledgeable, conversational)
  - Mode-specific execution instructions
  - **Does NOT contain** tool/function descriptions (moved to skills)

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

### Execution Modes

The agent supports two execution modes via the `--mode` flag:

**Direct Mode (Default)** - Efficient, token-saving:
```bash
python3 sdk_agent.py              # No flag needed
python3 sdk_agent.py --mode direct  # Explicit
```
- Uses Bash tool to call CLI dispatcher (sonos_tool.py)
- 21 discrete tools matching MCP functionality
- Calls `sonos_actions` functions via dispatcher
- ~15% token savings vs MCP mode
- Ideal for: Local development, complex workflows, batch operations

**MCP Mode** - Portable, standardized:
```bash
python3 sdk_agent.py --mode mcp
```
- Launches external MCP server process
- Uses 21 MCP tools via stdio protocol
- Compatible with Claude Desktop
- Ideal for: Multi-client scenarios, portability

### Running the Agent

**Interactive Mode** (conversation loop):
```bash
cd claude_sdk_agent

# Direct mode (default) - basic interactive usage
python3 sdk_agent.py

# MCP mode - explicit
python3 sdk_agent.py --mode mcp

# With verbose mode (shows tool/function calls)
python3 sdk_agent.py -v

# With logging
python3 sdk_agent.py -l session.log

# Resume a specific session
python3 sdk_agent.py -r abc123def456

# Continue most recent conversation
python3 sdk_agent.py -c

# Combine options (works in both modes)
python3 sdk_agent.py --mode direct -v -l debug.log
python3 sdk_agent.py --mode mcp -v -l debug.log
```

**Headless Mode** (single command execution):
```bash
# Direct mode (default) - execute a one-off command and exit
python3 sdk_agent.py -p "clear the queue and play playlist favorites"

# MCP mode - explicit
python3 sdk_agent.py --mode mcp -p "what's playing?"

# With verbose mode to see tool calls
python3 sdk_agent.py -v -p "what's playing?"

# With logging
python3 sdk_agent.py -l commands.log -p "turn it up"

# Resume session, add one command, and exit
python3 sdk_agent.py -r abc123 -p "play next track"

# Combine verbose and logging in headless mode
python3 sdk_agent.py -v -l headless.log -p "set volume to 50"

# Use in scripts or automation
python3 sdk_agent.py -p "play morning playlist" && echo "Music started!"
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
🎵 You: What playlists do I have?
🔧 [TOOL] list_playlists()
🤖 Assistant: Available playlists (3):
1. favorites
2. workout
3. chill

🎵 You: Add track 2 from the queue to my favorites playlist
🔧 [TOOL] add_to_playlist_from_queue(playlist='favorites', position=2)
🤖 Assistant: Added "Old Man" by Neil Young to your favorites playlist!
```

**Volume control:**
```
🎵 You: Turn it up
🔧 [TOOL] turn_volume(direction='louder')
🤖 Assistant: Volume increased by 10

🎵 You: Set volume to 40
🔧 [TOOL] set_volume(level=40)
🤖 Assistant: Volume set to 40
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

When adding new Sonos functionality, you need to update three layers:

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

4. **Update skill in `.claude/skills/sonos-control/SKILL.md`:**
   - Add tool to "Available MCP Tools" section
   - Include description, parameters, and usage notes
   - Add workflow examples showing when/how to use it
   - Update relevant sections (e.g., "Common Request Patterns")
   - **No agent code changes needed** - skill is auto-discovered

### Updating Skills

Skills can be updated independently without modifying agent code:

**To update the sonos-control skill:**
1. Edit `.claude/skills/sonos-control/SKILL.md`
2. Modify tool descriptions, workflows, or examples
3. Add/update reference files in `references/` directory
4. Test: Run agent and verify skill changes are reflected

**Skill changes take effect immediately** - the Agent SDK reads SKILL.md on each relevant request (progressive disclosure).

**When to update the skill vs system prompt:**
- **Update skill**: Tool usage, workflows, domain knowledge, examples
- **Update system prompt**: Agent personality, core behavior, general guidelines

**Skill best practices:**
- Keep YAML frontmatter concise (name + when to use description)
- Organize content with clear headings for easy navigation
- Provide specific examples for complex workflows
- Include error handling guidance
- Reference additional files for detailed information

### Working with the Dispatcher

The direct mode dispatcher (`sonos_tool.py`) provides a stable CLI interface for Sonos control. When adding functionality:

**To add a new tool:**

1. Add function to `sonos/sonos_actions.py` (if needed)
2. Add tool wrapper to `.claude/skills/sonos-direct-code/sonos_tool.py`:
   ```python
   @tool("your_tool_name")
   def your_tool_name(args):
       """Description of what this tool does."""
       if len(args) < 3:
           return "Error: required_arg required"

       # Parse arguments from sys.argv
       your_arg = args[2]

       try:
           # Call sonos_actions function
           result = sonos_actions.your_function(your_arg)
           return result if result else "Success message"
       except Exception as e:
           return handle_error(e, "your_tool_name")
   ```

3. Update `.claude/skills/sonos-direct-code/SKILL.md` with tool documentation:
   - Add to appropriate category section
   - Include usage example with full command path
   - Document parameters and expected behavior

4. Test from command line:
   ```bash
   .venv/bin/python3 .claude/skills/sonos-direct-code/sonos_tool.py your_tool_name test_arg
   ```

**Design principles:**
- **One tool = one action** - No multi-function tools
- **Accept CLI arguments** - Parse from `sys.argv` (args array)
- **Return formatted strings** - For agent consumption (not just success/failure)
- **User-friendly errors** - Specific, actionable error messages
- **Use 1-indexed positions** - For queue/playlist operations (more intuitive)
- **Stdout for results, stderr for errors** - Follow CLI conventions
- **Validate inputs early** - Check required args, ranges, types before calling functions

**Consistency with MCP:**
When adding dispatcher tools, ensure they match the corresponding MCP tool in `sonos_mcp_server/server.py`:
- Same tool name
- Same parameter order
- Same return format
- Same validation logic

This maintains parity between direct and MCP modes.

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
   - Lightweight system prompt for agent personality

4. **Domain knowledge** in `.claude/skills/sonos-control/SKILL.md`:
   - Tool descriptions and parameters
   - Workflows and usage patterns
   - Best practices and error handling
   - Auto-discovered by Agent SDK (no code changes needed)

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

The project supports two types of playlists:

#### Local Playlists

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

**Local Playlist Operations:**
- Create: Add first track to new playlist name
- View: `list_playlist_tracks`
- Edit: `add_to_playlist_*`, `remove_track_from_playlist`
- Play: `add_playlist_to_queue` (optionally with `shuffle=True` for randomized order)
- Save queue as playlist: Use `add_to_playlist_from_queue` for each track position

#### Native Sonos Playlists

Playlists stored on the Sonos system, accessible from:
- Sonos mobile app
- Other Sonos controllers
- Voice assistants (Alexa, Google Assistant)
- Any interface that talks to Sonos

**Native Playlist Operations:**
- List: `list_native_sonos_playlists`
- Convert from local: `create_native_sonos_playlist_from_local(local_playlist, native_name=None)`
  - Checks for naming conflicts automatically
  - Temporarily uses queue but restores original queue
  - Makes playlist accessible in Sonos app
- Future enhancements: Load to queue, delete, view tracks, sync with local

**Design Philosophy:**
- Local playlists: Convenient programmatic control and curation
- Native playlists: Broader ecosystem access (apps, voice, etc.)
- Both types are independent - changes to one don't affect the other

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

### Headless Mode

Execute single commands without entering interactive conversation loop:

```bash
# One-off command
python3 sdk_agent.py -p "clear the queue and play playlist favorites"

# Output: Task completion message, then exits
```

**Use Cases:**
- Shell scripts and automation
- Cron jobs for scheduled music
- Integration with other tools
- Quick commands without conversation UI

**Features Preserved:**
- Verbose mode (`-v`) - shows tool calls during execution
- Logging (`-l`) - records headless session to file
- Session management (`-r`, `-c`) - can resume/continue sessions
- All MCP tools work identically

**Example Scripts:**
```bash
#!/bin/bash
# Morning music routine
python3 sdk_agent.py -p "set volume to 30"
python3 sdk_agent.py -p "play morning playlist"

# Evening wind-down
python3 sdk_agent.py -p "set volume to 20"
python3 sdk_agent.py -p "play chill playlist"
```

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

- **Agent Skills**: https://www.anthropic.com/news/skills
- **Agent Skills Documentation**: https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills
- **Claude Agent SDK**: https://docs.anthropic.com/en/api/agent-sdk
- **MCP Protocol**: https://modelcontextprotocol.io/
- **SoCo Library**: https://github.com/SoCo/SoCo
- **FastMCP**: https://docs.modelcontextprotocol.io/docs/tools/fastmcp
- **Anthropic API**: https://docs.anthropic.com/

## Project Status

**Production Ready**: The MCP server architecture is fully implemented, tested, and ready for use with:
- Claude Agent SDK (current implementation)
- Claude Desktop (configuration provided)
- MCP Inspector (for testing)
- Any MCP-compatible client

All 21 tools are functional and tested end-to-end.
