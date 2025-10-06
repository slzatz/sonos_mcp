# Sonos Claude SDK Agent

A Sonos Claude Agent using the official **Claude Agent SDK**.

**SDK approach:**
- `ClaudeSDKClient` handles all conversation management
- Automatic tool execution via MCP server
- Uses sonos mcp server
- Built-in message loop

## Installation

### Prerequisites

1. **Claude Code CLI** must be installed:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

2. **Anthropic API Key** must be set:
   ```bash
   export ANTHROPIC_API_KEY='your-api-key-here'
   ```

### Install Dependencies

From the `claude_sdk_agent/` directory:

```bash
pip install -r requirements.txt
```

Or if using `uv` (recommended):

```bash
uv pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
cd claude_sdk_agent
python3 sdk_agent.py
```

### Verbose Mode

Show tool calls during conversation:

```bash
python3 sdk_agent.py -v
# or
python3 sdk_agent.py --verbose
```

**Example verbose output:**
```
🎵 You: play like a hurricane by neil young
🔧 [TOOL] search_for_track(query='like a hurricane neil young')
🔧 [TOOL] add_track_to_queue(position=9)
🔧 [TOOL] show_queue()
🔧 [TOOL] play_from_queue(position=49)
🤖 Assistant: Now playing "Like a Hurricane" by Neil Young!
```

### Logging

Log conversations to a file:

```bash
python3 sdk_agent.py -l                    # logs to sdk_agent.log
python3 sdk_agent.py -l my_session.log     # logs to custom file
python3 sdk_agent.py -v -l session.log     # verbose + logging
```

### Session Resumption

Continue previous conversations using session IDs:

#### Resume a Specific Session

```bash
# First conversation
python3 sdk_agent.py
🎵 You: Play some Neil Young
🤖 Assistant: I've added "Heart of Gold" to the queue...
🎵 You: quit

📋 Session ID: 1a2b3c4d-5e6f-7g8h-9i0j-k1l2m3n4o5p6
   (Use -r 1a2b3c4d-5e6f-7g8h-9i0j-k1l2m3n4o5p6 to resume this conversation)
👋 Goodbye! Enjoy your music!

# Later (same day, next week, etc.)
python3 sdk_agent.py -r 1a2b3c4d-5e6f-7g8h-9i0j-k1l2m3n4o5p6
🔄 Resuming session: 1a2b3c4d-5e6f-7g8h-9i0j-k1l2m3n4o5p6

🎵 You: What was I listening to?
🤖 Assistant: You were listening to "Heart of Gold" by Neil Young that I added earlier!
```

#### Continue Most Recent Conversation

```bash
# Skip typing the session ID - just continue the last conversation
python3 sdk_agent.py -c
🔄 Continuing most recent conversation

🎵 You: Add another Neil Young track
🤖 Assistant: I'll add "Old Man" to the queue!
```

#### Combine with Other Options

```bash
# Resume with verbose mode
python3 sdk_agent.py -r 1a2b3c4d-5e6f-7g8h-9i0j-k1l2m3n4o5p6 -v

# Continue with logging
python3 sdk_agent.py -c -l resumed_session.log

# Resume with all options
python3 sdk_agent.py -r 1a2b3c4d-5e6f-7g8h-9i0j-k1l2m3n4o5p6 -v -l
```

## Architecture

### File Structure

```
claude_sdk_agent/
├── sdk_agent.py           # Main agent using ClaudeSDKClient (~200 lines)
├── system_prompt.py       # System prompt (same as original)
├── requirements.txt       # SDK dependencies
└── README.md             # This file
```

### Component Breakdown

#### uses `sonos_mcp_server.py`
- THe mcp server Defines 17+ Sonos tools r

#### `sdk_agent.py`
- Uses `ClaudeSDKClient` for conversation management
- Configures `ClaudeAgentOptions` with MCP server and tools
- Handles user interaction and display
- Supports verbose mode and logging

#### Flow

```
User Input → ClaudeSDKClient → MCP Server → Tool Functions → Sonos CLI → Speakers
              ↑                                                               ↓
              └──────────────── Response with results ───────────────────────┘
```

## Comparison with Original

## Advanced Features (Future Enhancements)

The SDK enables features not easily possible in the original:

### 1. Interrupts
```python
# Stop a long-running operation
await agent.client.interrupt()
```

### 2. Hooks
```python
# Intercept tool calls for logging, validation, or modification
async def log_tool_hook(input_data, tool_use_id, context):
    print(f"Tool called: {input_data['tool_name']}")
    return {}

options = ClaudeAgentOptions(
    hooks={'PreToolUse': [HookMatcher(hooks=[log_tool_hook])]}
)
```

### 3. Session Resumption
```python
# Resume a previous conversation
options = ClaudeAgentOptions(resume="session_123")
```

### 4. Subagents
```python
# Delegate complex tasks to specialized agents
options = ClaudeAgentOptions(
    agents={
        "playlist_curator": AgentDefinition(
            description="Expert at creating playlists",
            prompt="You are a music curator...",
            tools=["search_for_track", "add_track_to_queue"]
        )
    }
)
```

## Troubleshooting

### "Claude Code not found" Error

Install the Claude Code CLI:
```bash
npm install -g @anthropic-ai/claude-code
```

### Tool Execution Errors

The SDK uses tool names prefixed with `mcp__sonos__`. If you see errors, verify:
1. All tools are listed in `allowed_tools` with the `mcp__sonos__` prefix
2. Tool names match between decorator and server registration

## Future Development

This proof-of-concept demonstrates the SDK's capabilities. Potential enhancements:

1. **Add file operations**: Read/write playlists from disk
2. **Add additional commands**: System volume control, speaker discovery
3. **Multi-turn workflows**: Complex playlist curation with interrupts
4. **Hook-based analytics**: Track usage patterns, popular searches
5. **Session persistence**: Save and resume music sessions

