#!/home/slzatz/sonos_cli/.venv/bin/python3

"""
Sonos Claude Agent - A natural language interface to Sonos speakers using Claude SDK.

This agent allows users to control their Sonos system through conversational commands
by leveraging the existing sonos CLI through Claude's function calling capabilities.
"""

import os
import sys
import argparse
from typing import Dict, Any, List
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
    def __init__(self, api_key: str = None, verbose: bool = False):
        """
        Initialize the Sonos Claude agent.

        Args:
            api_key: Anthropic API key. If not provided, will look for ANTHROPIC_API_KEY env var.
            verbose: If True, show tool calls and results during conversation.
        """
        if api_key is None:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = Anthropic(api_key=api_key)
        self.verbose = verbose
        self.conversation_history = []

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

        # Show tool call in verbose mode
        if self.verbose:
            if tool_input:
                params = ", ".join([f"{k}={repr(v)}" for k, v in tool_input.items()])
                print(f"🔧 [TOOL] {tool_name}({params})")
            else:
                print(f"🔧 [TOOL] {tool_name}()")

        try:
            # Call the appropriate function with the provided arguments
            if tool_name in ['search_track', 'search_album']:
                result = tool_function(tool_input['query'])
            elif tool_name in ['select_from_list', 'play_from_queue']:
                result = tool_function(tool_input['position'])
            else:
                # Tools with no parameters
                result = tool_function()

            # Show summarized result in verbose mode
            if self.verbose and result:
                summary = self._summarize_result(tool_name, result)
                print(f"📋 [RESULT] {summary}")

            return result if result else "Command executed successfully"
        except Exception as e:
            error_msg = f"Error executing {tool_name}: {str(e)}"
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
        if tool_name in ['search_track', 'search_album']:
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

        elif tool_name in ['play_from_queue', 'select_from_list']:
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
        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": user_message})

        try:
            return self._process_claude_response()
        except Exception as e:
            return f"Error communicating with Claude: {str(e)}"

    def _process_claude_response(self) -> str:
        """
        Process a Claude response, handling all tool calls properly.
        This method recursively handles tool calls until Claude gives a final text response.
        """
        # Make the API call with tools
        response = self.client.messages.create(
            model="claude-4-sonnet-20250514",
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
    args = parser.parse_args()

    print("🎵 Sonos Claude Agent")
    print("=" * 40)
    print("Welcome! I can help you control your Sonos speakers.")
    if args.verbose:
        print("🔧 Verbose mode enabled - tool calls will be shown")
    print("Try commands like:")
    print("  - 'Play some Neil Young'")
    print("  - 'What's currently playing?'")
    print("  - 'Show me the queue'")
    print("  - 'Skip to the next song'")
    print("\nType 'quit' or 'exit' to stop.\n")

    # Check for API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ Error: Please set your ANTHROPIC_API_KEY environment variable")
        print("   export ANTHROPIC_API_KEY='your-api-key-here'")
        return

    try:
        agent = SonosAgent(verbose=args.verbose)

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

    except Exception as e:
        print(f"❌ Failed to initialize agent: {str(e)}")

if __name__ == "__main__":
    main()
