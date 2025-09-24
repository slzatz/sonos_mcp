#!/home/slzatz/sonos_cli/.venv/bin/python3

"""
Sonos Claude Agent - A natural language interface to Sonos speakers using Claude SDK.

This agent allows users to control their Sonos system through conversational commands
by leveraging the existing sonos CLI through Claude's function calling capabilities.
"""

import os
import sys
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
    def __init__(self, api_key: str = None):
        """
        Initialize the Sonos Claude agent.

        Args:
            api_key: Anthropic API key. If not provided, will look for ANTHROPIC_API_KEY env var.
        """
        if api_key is None:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = Anthropic(api_key=api_key)
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

        try:
            # Call the appropriate function with the provided arguments
            if tool_name in ['search_track', 'search_album']:
                result = tool_function(tool_input['query'])
            elif tool_name == 'select_track':
                result = tool_function(tool_input['position'])
            else:
                # Tools with no parameters
                result = tool_function()

            return result if result else "Command executed successfully"
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

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
            # Make the API call with tools
            response = self.client.messages.create(
                #model="claude-3-5-sonnet-20241022",
                model="claude-4-sonnet-20250514",
                max_tokens=1000,
                system=SONOS_SYSTEM_PROMPT,
                messages=self.conversation_history,
                tools=SONOS_TOOLS
            )

            # Process the response
            assistant_message = {"role": "assistant", "content": []}
            response_text = ""

            for content_block in response.content:
                if content_block.type == "text":
                    response_text += content_block.text
                    assistant_message["content"].append(content_block)
                elif content_block.type == "tool_use":
                    # Execute the tool
                    tool_result = self.handle_tool_call(
                        content_block.name,
                        content_block.input
                    )

                    # Add tool use to conversation
                    assistant_message["content"].append(content_block)

                    # Add tool result as a separate message
                    tool_result_message = {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": content_block.id,
                                "content": tool_result
                            }
                        ]
                    }

                    # Add both messages to history
                    self.conversation_history.append(assistant_message)
                    self.conversation_history.append(tool_result_message)

                    # Get follow-up response from Claude
                    follow_up = self.client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=1000,
                        system=SONOS_SYSTEM_PROMPT,
                        messages=self.conversation_history,
                        tools=SONOS_TOOLS
                    )

                    # Return the follow-up response
                    final_response = ""
                    for block in follow_up.content:
                        if block.type == "text":
                            final_response += block.text

                    # Add to conversation history
                    self.conversation_history.append({"role": "assistant", "content": follow_up.content})
                    return final_response

            # If no tools were used, just return the text response
            if response_text:
                self.conversation_history.append(assistant_message)
                return response_text

            return "I'm not sure how to respond to that."

        except Exception as e:
            return f"Error communicating with Claude: {str(e)}"

def main():
    """Main function to run the Sonos agent interactively."""
    print("🎵 Sonos Claude Agent")
    print("=" * 40)
    print("Welcome! I can help you control your Sonos speakers.")
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
        agent = SonosAgent()

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
