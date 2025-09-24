# Sonos Claude Agent 🎵

A natural language interface to control Sonos speakers using the Claude SDK. This agent wraps your existing Sonos CLI to provide conversational music control.

## Features

- **Natural Language Control**: "Play some Neil Young" instead of remembering CLI commands
- **Smart Search**: Finds tracks and albums using conversational queries
- **Queue Management**: View, clear, and control your music queue
- **Playback Control**: Play, pause, skip tracks with simple commands
- **Current Status**: Always know what's playing and what's queued up

## Project Structure

```
sonos_agent/
├── sonos_agent.py     # Main agent application
├── sonos_tools.py     # CLI tool wrappers
├── system_prompt.py   # Claude system prompt
├── test_tools.py      # Tool testing script
├── requirements.txt   # Dependencies
└── README.md         # This file
```

## Prerequisites

1. **Working Sonos CLI**: Your existing `sonos` command must be functional
2. **Claude API Key**: You need an Anthropic API key for Claude
3. **Python 3.8+**: The agent requires modern Python

## Setup

1. **Install Dependencies**:
   ```bash
   cd sonos_agent
   pip install -r requirements.txt
   ```

2. **Set Your API Key**:
   ```bash
   export ANTHROPIC_API_KEY='your-api-key-here'
   ```

3. **Test Your Sonos CLI** (make sure this works first):
   ```bash
   sonos what        # Should show current track or "nothing playing"
   sonos showqueue   # Should show your queue
   ```

4. **Test the Agent Tools**:
   ```bash
   python3 test_tools.py
   ```

## Usage

Run the interactive agent:

```bash
python3 sonos_agent.py
```

### Example Conversations

```
🎵 You: Play some Neil Young
🤖 Assistant: I'll search for Neil Young tracks for you.
[searches and shows results]
Which one would you like, or should I start with the first one?

🎵 You: Play the first one
🤖 Assistant: I've added "Harvest Moon - Neil Young" to your queue!

🎵 You: What's playing now?
🤖 Assistant: [shows current track info]

🎵 You: Show me what's in the queue
🤖 Assistant: [displays complete queue]

🎵 You: Skip to the next song
🤖 Assistant: Skipped to the next track!
```

### Supported Commands

- **Search & Play**: "Play Harvest by Neil Young", "Find some Beatles songs"
- **Current Status**: "What's playing?", "What song is this?"
- **Queue Management**: "Show the queue", "Clear the queue"
- **Playback Control**: "Pause", "Play", "Next song", "Skip this"
- **Albums**: "Play the Abbey Road album", "Find Pink Floyd albums"

## How It Works

1. **Tool Wrappers**: The `sonos_tools.py` module wraps your CLI commands as Python functions
2. **Claude Integration**: Claude calls these tools based on your natural language requests
3. **Conversation Flow**: The agent maintains context and handles multi-step workflows
4. **Error Handling**: Gracefully handles CLI errors and API issues

## Troubleshooting

### "AuthTokenExpired" Errors
If search fails with authentication errors, your music service (Amazon Music, etc.) needs re-authentication. Fix this in your main Sonos CLI first.

### "Nothing appears to be playing"
This is normal when no music is currently playing. The agent can still search and queue music.

### API Key Issues
Make sure your `ANTHROPIC_API_KEY` environment variable is set correctly.

### CLI Not Found
Ensure your `sonos` command is in your PATH and working properly.

## Architecture

```
User Input → Claude Agent → Tool Selection → Sonos CLI → Sonos Speakers
    ↓              ↓              ↓              ↓              ↓
"Play Neil    Calls         Executes      CLI sends       Music
 Young"    search_track()   `sonos         commands        plays
                            searchtrack`   to speakers
```

## Extending the Agent

### Adding New Tools
1. Add CLI wrapper function to `sonos_tools.py`
2. Add tool definition to `SONOS_TOOLS` list
3. Update `get_tool_function()` mapping

### Customizing Behavior
Edit `system_prompt.py` to change how the agent responds and behaves.

### Advanced Features
Consider adding:
- Playlist management
- Volume control
- Multi-room grouping
- Music recommendations
- Voice input integration

## Limitations

- Requires working Sonos CLI setup
- Limited by your music service authentication
- Search quality depends on your music service
- No direct Sonos API integration (uses CLI wrapper)

## Next Steps

This proof-of-concept demonstrates the feasibility of using Claude SDK with your Sonos system. You could extend it to:

- **Voice Integration**: Add speech-to-text for voice control
- **Web Interface**: Create a web app wrapper
- **Smart Home**: Integrate with home automation systems
- **Music AI**: Add intelligent playlist generation
- **Multi-User**: Support different user preferences

## Support

If you encounter issues:
1. Test your base `sonos` CLI commands first
2. Check the `test_tools.py` output for tool wrapper issues
3. Verify your Claude API key is working
4. Check that your music service authentication is valid

The agent leverages your existing, working Sonos setup - so if the CLI works, the agent should work too!