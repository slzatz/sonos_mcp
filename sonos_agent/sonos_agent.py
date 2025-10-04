#!/home/slzatz/sonos_cli/.venv/bin/python3

"""
Sonos Claude Agent - A natural language interface to Sonos speakers using Claude SDK.

This agent allows users to control their Sonos system through conversational commands
by leveraging the existing sonos CLI through Claude's function calling capabilities.
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import anthropic
from anthropic import Anthropic

# Import our local modules
from sonos_tools import SONOS_TOOLS, get_tool_function
from system_prompt import SONOS_SYSTEM_PROMPT

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class SonosAgent:
    def __init__(self, api_key: str = None, verbose: bool = False, log_file: str = None):
        """
        Initialize the Sonos Claude agent.

        Args:
            api_key: Anthropic API key. If not provided, will look for ANTHROPIC_API_KEY env var.
            verbose: If True, show tool calls and results during conversation.
            log_file: Path to log file for conversation logging. If None, no logging.
        """
        if api_key is None:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = Anthropic(api_key=api_key)
        self.verbose = verbose
        self.log_file = log_file
        self.logger = None
        self.conversation_history = []

        # Set up logging if log file is provided
        if log_file:
            self._setup_logging()

    def _setup_logging(self):
        """
        Set up logging configuration for conversation logging.
        """
        # Create a logger instance for this agent
        self.logger = logging.getLogger(f'sonos_agent_{id(self)}')
        self.logger.setLevel(logging.INFO)

        # Remove any existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Create file handler with append mode
        file_handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # Create formatter
        #formatter = logging.Formatter('%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s',
                                    datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)

        # Add handler to logger
        self.logger.addHandler(file_handler)

        # Log session start
        self.logger.info("SESSION_START: Sonos Claude Agent session beginning")

    def _log_user_input(self, message: str):
        """Log user input message."""
        if self.logger:
            self.logger.info(f"[USER] {message}")

    def _log_tool_call(self, tool_name: str, tool_input: Dict[str, Any]):
        """Log tool call with parameters."""
        if self.logger:
            if tool_input:
                params = ", ".join([f"{k}={repr(v)}" for k, v in tool_input.items()])
                self.logger.info(f"[TOOL] {tool_name}({params})")
            else:
                self.logger.info(f"[TOOL] {tool_name}()")

    def _log_tool_result(self, tool_name: str, result: str):
        """Log tool execution result."""
        if self.logger:
            summary = self._summarize_result(tool_name, result)
            self.logger.info(f"[RESULT] {summary}")

    def _log_assistant_response(self, response: str):
        """Log assistant response."""
        if self.logger:
            # Truncate very long responses for logging
            logged_response = response[:500] + "..." if len(response) > 500 else response
            self.logger.info(f"[ASSISTANT] {logged_response}")

    def _log_error(self, error_msg: str):
        """Log error message."""
        if self.logger:
            self.logger.error(f"[ERROR] {error_msg}")

    def _log_session_end(self):
        """Log session end marker."""
        if self.logger:
            self.logger.info("SESSION_END: Sonos Claude Agent session ending")

    def handle_tool_call(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Execute a tool call and return the result.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Tool execution result as string
        """
        tool_function = get_tool_function(tool_name)
        if not tool_function:
            return f"Error: Unknown tool '{tool_name}'"

        # Log tool call
        self._log_tool_call(tool_name, tool_input)

        # Show tool call in verbose mode
        if self.verbose:
            if tool_input:
                params = ", ".join([f"{k}={repr(v)}" for k, v in tool_input.items()])
                print(f"🔧 [TOOL] {tool_name}({params})")
            else:
                print(f"🔧 [TOOL] {tool_name}()")

        try:
            # Call the appropriate function with the provided arguments
            if tool_name in ['search_for_track', 'search_for_album']:
                result = tool_function(tool_input['query'])
            elif tool_name in ['add_playlist_to_queue']:
                result = tool_function(tool_input['playlist'])
            elif tool_name in ['add_track_to_queue', 'add_album_to_queue', 'play_from_queue']:
                result = tool_function(tool_input['position'])
            elif tool_name in ['add_to_playlist_from_search', 'add_to_playlist_from_queue']:
                result = tool_function(tool_input['playlist'], tool_input['position'])
            else:
                # Tools with no parameters
                result = tool_function()

            # Log tool result
            self._log_tool_result(tool_name, result)

            # Show summarized result in verbose mode
            if self.verbose and result:
                summary = self._summarize_result(tool_name, result)
                print(f"📋 [RESULT] {summary}")

            return result if result else "Command executed successfully"
        except Exception as e:
            error_msg = f"Error executing {tool_name}: {str(e)}"

            # Log error
            self._log_error(error_msg)

            if self.verbose:
                print(f"❌ [ERROR] {error_msg}")
            return error_msg

    def _summarize_result(self, tool_name: str, result: str) -> str:
        """
        Create a concise summary of tool results for verbose mode.

        Args:
            tool_name: Name of the tool that was executed
            result: The full result string from the tool

        Returns:
            A summarized version of the result
        """
        if not result:
            return "No output"

        # Tool-specific summarization (BEFORE any truncation)
        if tool_name in ['search_for_track', 'search_for_album']:
            lines = result.strip().split('\n')
            if len(lines) > 1:
                # Count results and show first few
                count = len(lines)
                first_few = ', '.join([line.split('. ', 1)[1] if '. ' in line else line
                                     for line in lines[:3] if line.strip()])
                return f"Found {count} results: {first_few}{'...' if count > 3 else ''}"
            # Fall through to truncation for single-line results

        elif tool_name == 'show_queue':
            lines = result.strip().split('\n')
            # Count ALL tracks before any truncation
            count = len([line for line in lines if line.strip() and '. ' in line])
            if count > 0:
                return f"Queue contains {count} tracks"
            # Fall through to truncation if count is 0

        elif tool_name == 'current_track':
            # Keep current track info concise but informative
            if "Nothing appears to be playing" in result:
                return "Nothing playing"
            return result

        elif tool_name in ['play_from_queue', 'add_track_to_queue', 'add_album_to_queue']:
            # Show what was selected/played
            if '{' in result and '}' in result:
                # Extract track info from JSON-like response
                try:
                    import re
                    title_match = re.search(r"'title': '([^']*)'", result)
                    artist_match = re.search(r"'artist': '([^']*)'", result)
                    if title_match and artist_match:
                        return f"'{title_match.group(1)}' by {artist_match.group(1)}"
                except:
                    pass
            return result

        # Default: truncate long results for tools not specifically handled above
        if len(result) > 200:
            return result[:200] + "..."
        return result

    def chat(self, user_message: str) -> str:
        """
        Send a message to Claude and handle any tool calls.

        Args:
            user_message: The user's input message

        Returns:
            Claude's response after processing any tool calls
        """
        # Log user input
        self._log_user_input(user_message)

        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": user_message})

        try:
            response = self._process_claude_response()
            # Log assistant response
            self._log_assistant_response(response)
            return response
        except Exception as e:
            error_msg = f"Error communicating with Claude: {str(e)}"
            self._log_error(error_msg)
            return error_msg

    def _process_claude_response(self) -> str:
        """
        Process a Claude response, handling all tool calls properly.
        This method recursively handles tool calls until Claude gives a final text response.
        """
        # Make the API call with tools
        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1000,
            system=SONOS_SYSTEM_PROMPT,
            messages=self.conversation_history,
            tools=SONOS_TOOLS
        )

        # Separate text and tool calls
        text_content = []
        tool_calls = []

        for content_block in response.content:
            if content_block.type == "text":
                text_content.append(content_block)
            elif content_block.type == "tool_use":
                tool_calls.append(content_block)

        # Build assistant message
        assistant_message = {"role": "assistant", "content": response.content}

        # If there are tool calls, we need to execute them and get follow-up response
        if tool_calls:
            # Add assistant message to history
            self.conversation_history.append(assistant_message)

            # Execute all tool calls and create tool result messages
            for tool_call in tool_calls:
                tool_result = self.handle_tool_call(
                    tool_call.name,
                    tool_call.input
                )

                # Add tool result message
                tool_result_message = {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_call.id,
                            "content": tool_result
                        }
                    ]
                }
                self.conversation_history.append(tool_result_message)

            # Recursively process Claude's follow-up response
            return self._process_claude_response()

        else:
            # No tool calls - this is the final response
            self.conversation_history.append(assistant_message)

            # Extract text from content blocks
            response_text = ""
            for block in text_content:
                response_text += block.text

            return response_text if response_text else "I'm not sure how to respond to that."

def main():
    """Main function to run the Sonos agent interactively."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Sonos Claude Agent - Natural language control for Sonos speakers")
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show tool calls and results during conversation')
    parser.add_argument('-l', '--log', nargs='?', const='sonos_agent.log', metavar='LOG_FILE',
                       help='Log conversation to file (default: sonos_agent.log)')
    args = parser.parse_args()

    print("🎵 Sonos Claude Agent")
    print("=" * 40)
    if args.verbose:
        print("🔧 Verbose mode enabled - tool calls will be shown")
    if args.log:
        print(f"📝 Logging enabled - conversations saved to: {args.log}")
    print("\nType 'quit' or 'exit' to stop.\n")

    # Check for API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ Error: Please set your ANTHROPIC_API_KEY environment variable")
        print("   export ANTHROPIC_API_KEY='your-api-key-here'")
        return

    try:
        agent = SonosAgent(verbose=args.verbose, log_file=args.log)

        try:
            while True:
                try:
                    user_input = input("\n🎵 You: ").strip()

                    if user_input.lower() in ['quit', 'exit', 'bye']:
                        print("👋 Goodbye! Enjoy your music!")
                        break

                    if not user_input:
                        continue

                    print("🤖 Assistant: ", end="", flush=True)
                    response = agent.chat(user_input)
                    print(response)

                except KeyboardInterrupt:
                    print("\n👋 Goodbye! Enjoy your music!")
                    break
                except Exception as e:
                    print(f"❌ Error: {str(e)}")
        finally:
            # Log session end
            agent._log_session_end()

    except Exception as e:
        print(f"❌ Failed to initialize agent: {str(e)}")

if __name__ == "__main__":
    main()
