#!/home/slzatz/sonos_mcp/.venv/bin/python3

"""
Sonos Claude SDK Agent - A natural language interface using Claude Agent SDK.

This is a rewrite of the original sonos_agent.py using the official Claude Agent SDK.
It provides the same functionality with significantly less code by leveraging:
- ClaudeSDKClient for conversation management
- @tool decorator for tool definitions
- MCP server for tool registration
"""

import os
import sys
import argparse
import asyncio
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock, ToolUseBlock, ResultMessage

# Import our local modules
from system_prompt import SONOS_SYSTEM_PROMPT

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class SonosSDKAgent:
    """Sonos agent using Claude Agent SDK."""

    def __init__(self, verbose: bool = False, log_file: Optional[str] = None,
                 resume_session: Optional[str] = None, continue_conversation: bool = False):
        """
        Initialize the Sonos Claude SDK agent.

        Args:
            verbose: If True, show tool calls and results during conversation.
            log_file: Path to log file for conversation logging. If None, no logging.
            resume_session: Session ID to resume. If provided, continues that specific session.
            continue_conversation: If True, continues the most recent conversation.
        """
        # Set up logging if requested
        self.logger = None
        if log_file:
            self._setup_logging(log_file)

        self.verbose = verbose
        self.session_id = None  # Will be set after first interaction

        # Configure external Sonos MCP server (stdio transport)
        project_root = Path(__file__).parent.parent
        server_path = project_root / "sonos_mcp_server" / "server.py"
        venv_python = project_root / ".venv" / "bin" / "python3"

        # Configure Claude Agent options
        self.options = ClaudeAgentOptions(
            mcp_servers={
                "sonos": {
                    "command": str(venv_python),
                    "args": [str(server_path)]
                }
            },
            allowed_tools=[
                # Speaker management
                "mcp__sonos__get_master_speaker",
                "mcp__sonos__set_master_speaker",
                # Music search
                "mcp__sonos__search_for_track",
                "mcp__sonos__search_for_album",
                # Queue management
                "mcp__sonos__add_track_to_queue",
                "mcp__sonos__add_album_to_queue",
                "mcp__sonos__list_queue",
                "mcp__sonos__clear_queue",
                "mcp__sonos__play_from_queue",
                # Playback control
                "mcp__sonos__current_track",
                "mcp__sonos__play_pause",
                "mcp__sonos__next_track",
                # Playlist management
                "mcp__sonos__add_to_playlist_from_queue",
                "mcp__sonos__add_to_playlist_from_search",
                "mcp__sonos__add_playlist_to_queue",
                "mcp__sonos__list_playlist_tracks",
                "mcp__sonos__remove_track_from_playlist"
            ],
            system_prompt=SONOS_SYSTEM_PROMPT,
            # model parameter omitted - uses Claude Code CLI default (Claude Sonnet 4.5)
            permission_mode="bypassPermissions",  # Auto-execute tools without prompting
            resume=resume_session if resume_session else None,
            continue_conversation=continue_conversation
        )

        # Create the client
        self.client = ClaudeSDKClient(options=self.options)

    def _setup_logging(self, log_file: str):
        """Set up logging configuration for conversation logging."""
        self.logger = logging.getLogger(f'sonos_sdk_agent_{id(self)}')
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()

        file_path = Path.home() / ".sonos" / "logs" / log_file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(file_path, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.info("SESSION_START: Sonos Claude SDK Agent session beginning")

    def _log(self, level: str, message: str):
        """Log a message if logging is enabled."""
        if self.logger:
            if level == "INFO":
                self.logger.info(message)
            elif level == "ERROR":
                self.logger.error(message)

    async def chat(self, user_message: str) -> str:
        """
        Send a message to Claude and get a response.

        Args:
            user_message: The user's input message

        Returns:
            Claude's response text
        """
        # Log user input
        self._log("INFO", f"[USER] {user_message}")

        try:
            # Send query to Claude
            await self.client.query(user_message)

            # Collect response
            response_text = ""

            # Process all messages until we get the final response
            async for message in self.client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            response_text += block.text
                        elif isinstance(block, ToolUseBlock) and self.verbose:
                            # Show tool call in verbose mode
                            params = ", ".join([f"{k}={repr(v)}" for k, v in block.input.items()])
                            tool_name = block.name.replace("mcp__sonos__", "")
                            print(f"🔧 [TOOL] {tool_name}({params})")
                            self._log("INFO", f"[TOOL] {tool_name}({params})")
                elif isinstance(message, ResultMessage):
                    # Capture session ID from result message and log if first time
                    if message.session_id and not self.session_id:
                        self._log("INFO", f"[SESSION_ID] {message.session_id}")
                    self.session_id = message.session_id

            # Log assistant response
            self._log("INFO", f"[ASSISTANT] {response_text[:1500]}{'...' if len(response_text) > 1500 else ''}")

            return response_text if response_text else "I'm not sure how to respond to that."

        except Exception as e:
            error_msg = f"Error communicating with Claude: {str(e)}"
            self._log("ERROR", f"[ERROR] {error_msg}")
            return error_msg

    async def start(self):
        """Connect to Claude and start the agent."""
        await self.client.connect()

    async def stop(self):
        """Disconnect from Claude and cleanup."""
        if self.session_id:
            self._log("INFO", f"[SESSION_ID] {self.session_id} (resume with -r {self.session_id})")
        self._log("INFO", "SESSION_END: Sonos Claude SDK Agent session ending")
        await self.client.disconnect()


async def main():
    """Main function to run the Sonos SDK agent interactively."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Sonos Claude SDK Agent - Natural language control for Sonos speakers"
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show tool calls and results during conversation'
    )
    parser.add_argument(
        '-l', '--log',
        nargs='?',
        const='sdk_agent.log',
        metavar='LOG_FILE',
        help='Log conversation to file (default: sdk_agent.log)'
    )
    parser.add_argument(
        '-r', '--resume',
        type=str,
        metavar='SESSION_ID',
        help='Resume a previous session by its ID'
    )
    parser.add_argument(
        '-c', '--continue-conversation',
        action='store_true',
        help='Continue the most recent conversation'
    )
    parser.add_argument(
        '-p', '--prompt',
        type=str,
        metavar='PROMPT',
        help='Execute a single prompt and exit (headless mode)'
    )
    args = parser.parse_args()

    print("🎵 Sonos Claude SDK Agent")
    print("=" * 40)
    if args.prompt:
        print("⚡ Headless mode - executing single prompt")
    if args.verbose:
        print("🔧 Verbose mode enabled - tool calls will be shown")
    if args.log:
        print(f"📝 Logging enabled - conversations saved to: {args.log}")
    if args.resume:
        print(f"🔄 Resuming session: {args.resume}")
    if args.continue_conversation:
        print("🔄 Continuing most recent conversation")
    if not args.prompt:
        print("\nType 'quit' or 'exit' to stop.\n")

    # Check for API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ Error: Please set your ANTHROPIC_API_KEY environment variable")
        print("   export ANTHROPIC_API_KEY='your-api-key-here'")
        return

    try:
        agent = SonosSDKAgent(
            verbose=args.verbose,
            log_file=args.log,
            resume_session=args.resume,
            continue_conversation=args.continue_conversation
        )
        await agent.start()

        try:
            # Headless mode - single prompt execution
            if args.prompt:
                response = await agent.chat(args.prompt)
                print(response)
                # Display session ID before exiting
                if agent.session_id:
                    print(f"\n📋 Session ID: {agent.session_id}", file=sys.stderr)
                return

            # Interactive mode - continuous conversation loop
            while True:
                try:
                    # Get user input
                    user_input = input("\n🎵 You: ").strip()

                    if user_input.lower() in ['quit', 'exit', 'bye']:
                        # Display session ID before exiting
                        if agent.session_id:
                            print(f"\n📋 Session ID: {agent.session_id}")
                            print(f"   (Use -r {agent.session_id} to resume this conversation)")
                        print("👋 Goodbye! Enjoy your music!")
                        break

                    if not user_input:
                        continue

                    # Get and display response
                    print("🤖 Assistant: ", end="", flush=True)
                    response = await agent.chat(user_input)
                    print(response)

                except KeyboardInterrupt:
                    # Display session ID on interrupt
                    if agent.session_id:
                        print(f"\n\n📋 Session ID: {agent.session_id}")
                        print(f"   (Use -r {agent.session_id} to resume this conversation)")
                    print("\n👋 Goodbye! Enjoy your music!")
                    break
                except Exception as e:
                    print(f"❌ Error: {str(e)}")

        finally:
            await agent.stop()

    except Exception as e:
        print(f"❌ Failed to initialize agent: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
