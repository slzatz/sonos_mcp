#!/usr/bin/env python3
"""
Interactive Sonos TUI for Track and Album Search and Playback

Experimental TUI designed to work with tmux for agent-driven interaction.
Supports search (tracks or albums) → select → add to queue → optional immediate playback workflow.
"""

import sys
import json
import os
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sonos import sonos_actions


class SonosInteractiveTUI:
    """Interactive TUI for Sonos control via tmux."""

    def __init__(self):
        self.search_results = []
        self.search_type = "track"  # Default to track search, can be "track" or "album"
        self.search_results_dir = Path.home() / ".sonos" / "search_results"
        self.search_results_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = Path.home() / ".sonos" / "tui_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def initialize_speaker(self):
        """Initialize speaker connection."""
        print("Initializing Sonos speaker...")
        try:
            sonos_actions.set_master()
            speaker_name = sonos_actions.master.player_name if sonos_actions.master else "Unknown"
            print(f"Connected to: {speaker_name}\n")
            return True
        except Exception as e:
            print(f"Error connecting to speaker: {e}")
            print("Please check your configuration and try again.")
            return False

    def write_state(self, status="running", current_prompt="search"):
        """Write current TUI state to state file."""
        try:
            state = {
                "status": status,
                "current_prompt": current_prompt,
                "pid": os.getpid(),
                "pane_id": os.getenv("TMUX_PANE", "unknown"),
                "last_updated": datetime.now().isoformat()
            }

            # Write atomically using temp file
            temp_file = self.state_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(state, f, indent=2)
            temp_file.replace(self.state_file)

        except Exception as e:
            # Don't crash TUI if state file write fails
            print(f"Warning: Could not write state file: {e}", file=sys.stderr)

    def display_search_results(self, results):
        """Display numbered search results."""
        if not results:
            print("No results found.")
            return

        print(f"\nFound {len(results)} results:")
        print("-" * 80)
        for i, result in enumerate(results, 1):
            title = result.get('title', 'Unknown')
            artist = result.get('artist', 'Unknown')
            album = result.get('album', 'Unknown')
            print(f"{i}. {title} - {artist} - {album}")
        print("-" * 80)

    def save_search_results(self, results):
        """Save search results to JSON file for compatibility."""
        try:
            with open(self.search_results_file, 'w') as f:
                json.dump(results, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save search results: {e}")

    def handle_search(self, query):
        """Execute search and display results."""
        if not query or query.strip() == '':
            print("Empty query. Please try again.")
            return False

        # Parse search type from query prefix
        # Accept both "album:" and "album " for robustness
        if query.lower().startswith("album:"):
            self.search_type = "album"
            actual_query = query[6:].strip()  # Remove "album:" prefix
        elif query.lower().startswith("album "):
            self.search_type = "album"
            actual_query = query[6:].strip()  # Remove "album " prefix
        else:
            self.search_type = "track"
            actual_query = query.strip()

        # Display what type of search we're performing
        print(f"\nSearching for {self.search_type}: {actual_query}")

        try:
            # Call appropriate search function based on type
            if self.search_type == "album":
                result_text = sonos_actions.search_for_album(actual_query)
                results_file = self.search_results_dir / "album_search.json"
            else:
                result_text = sonos_actions.search_for_track(actual_query)
                results_file = self.search_results_dir / "track_search.json"

            # Load the results from the JSON file that search function created
            if results_file.exists():
                with open(results_file) as f:
                    self.search_results = json.load(f)

                if self.search_results:
                    self.display_search_results(self.search_results)
                    return True
                else:
                    print("No results found.")
                    return False
            else:
                print("No results found.")
                return False

        except Exception as e:
            print(f"Search error: {e}")
            return False

    def handle_selection(self, selection_input):
        """Process track or album selection."""
        try:
            position = int(selection_input)
            if position < 1 or position > len(self.search_results):
                print(f"Invalid selection. Please choose 1-{len(self.search_results)}")
                return False

            # Get queue length BEFORE adding to determine start position
            queue_before = sonos_actions.list_queue()
            start_position = len(queue_before) + 1

            # Add to queue using appropriate function based on search type
            item_type = self.search_type
            print(f"\nAdding {item_type} {position} to queue...")

            if self.search_type == "album":
                result = sonos_actions.add_album_to_queue(position)
            else:
                result = sonos_actions.add_track_to_queue(position)

            if result:
                print(result)

            # Get current queue length to know position of newly added item(s)
            queue_after = sonos_actions.list_queue()
            end_position = len(queue_after)

            if self.search_type == "album":
                num_tracks = end_position - start_position + 1
                print(f"Album tracks added to queue (positions {start_position}-{end_position}, {num_tracks} tracks).")
                return start_position  # Play from first track of album
            else:
                print(f"Track added at position {end_position}.")
                return end_position  # For single tracks, start = end

        except ValueError:
            print("Invalid input. Please enter a number.")
            return False
        except Exception as e:
            print(f"Error adding {self.search_type}: {e}")
            return False

    def handle_play_choice(self, choice, queue_position):
        """Handle immediate playback choice."""
        if choice.lower() in ['y', 'yes']:
            try:
                if self.search_type == "album":
                    print(f"\nPlaying album from position {queue_position}...")
                else:
                    print(f"\nPlaying track from position {queue_position}...")
                # play_from_queue expects 0-indexed position
                result = sonos_actions.play_from_queue(queue_position - 1)
                if result:
                    print(result)
                else:
                    if self.search_type == "album":
                        print(f"Now playing album starting from track {queue_position}!")
                    else:
                        print(f"Now playing track {queue_position}!")
                return True
            except Exception as e:
                print(f"Error playing track: {e}")
                return False
        else:
            print("Track queued. Not playing immediately.")
            return True

    def main_loop(self):
        """Main interactive loop."""
        print("=" * 80)
        print("Sonos Interactive Track and Album Search")
        print("=" * 80)
        print("Commands: Type search query, track/album number, or 'quit' to exit\n")

        if not self.initialize_speaker():
            return

        # Write initial state after successful initialization
        self.write_state(status="running", current_prompt="search")

        while True:
            try:
                # State 1: Get search query
                query = input("Search: ").strip()

                if query.lower() in ['q', 'quit', 'exit']:
                    print("\nGoodbye!")
                    self.write_state(status="stopped", current_prompt="search")
                    break

                # Execute search
                if not self.handle_search(query):
                    continue

                # Update state after successful search
                self.write_state(status="running", current_prompt="select")

                # State 2: Get track/album selection
                selection = input(f"\nSelect {self.search_type} (1-{len(self.search_results)}) or 'q' to search again: ").strip()

                if selection.lower() in ['q', 'quit']:
                    print("Returning to search...\n")
                    self.write_state(status="running", current_prompt="search")
                    continue

                # Process selection
                queue_position = self.handle_selection(selection)
                if not queue_position:
                    continue

                # Update state before play decision
                self.write_state(status="running", current_prompt="play")

                # State 3: Ask about immediate playback
                play_choice = input("Play now? (y/n): ").strip()

                self.handle_play_choice(play_choice, queue_position)

                # Return to search state after completing the workflow
                self.write_state(status="running", current_prompt="search")

                print("\n" + "=" * 80 + "\n")

            except KeyboardInterrupt:
                print("\n\nInterrupted. Exiting...")
                self.write_state(status="stopped", current_prompt="search")
                break
            except EOFError:
                print("\n\nEOF received. Exiting...")
                self.write_state(status="stopped", current_prompt="search")
                break
            except Exception as e:
                print(f"\nUnexpected error: {e}")
                print("Returning to search...\n")
                # Keep running on unexpected errors, just reset to search state
                self.write_state(status="running", current_prompt="search")


def main():
    """Entry point."""
    tui = SonosInteractiveTUI()
    tui.main_loop()


if __name__ == "__main__":
    main()
