#!/usr/bin/env python3
"""
Sonos Tool Dispatcher for Direct Mode

Exposes sonos_actions functions as discrete command-line tools.
Usage: sonos_tool.py <tool_name> [args...]

This dispatcher provides 21 tools matching the MCP server functionality,
but executes directly without MCP protocol overhead for token efficiency.
"""

import sys
import json
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sonos import sonos_actions


def initialize_speaker():
    """Ensure speaker is initialized before operations."""
    try:
        sonos_actions.set_master()
    except Exception as e:
        print(f"Error initializing speaker: {e}", file=sys.stderr)
        sys.exit(1)


def handle_error(e: Exception, tool_name: str):
    """Standardized error handling for all tools."""
    error_msg = f"Error in {tool_name}: {str(e)}"
    print(error_msg, file=sys.stderr)
    return error_msg


# Tool registry: Maps tool names to (function, arg_parser) tuples
# arg_parser is a function that takes sys.argv and returns args for the sonos_actions function
TOOLS = {}


def tool(name):
    """Decorator to register tools."""
    def decorator(func):
        TOOLS[name] = func
        return func
    return decorator


# Speaker Management Tools

@tool("get_master_speaker")
def get_master_speaker(args):
    """Get the currently configured master speaker name."""
    # Try to initialize if not already done
    if not hasattr(sonos_actions, 'master') or sonos_actions.master is None:
        sonos_actions.set_master()

    if sonos_actions.master:
        return f"Current master speaker: {sonos_actions.master.player_name}"
    return "No speaker connected"


@tool("set_master_speaker")
def set_master_speaker(args):
    """Change the master speaker to a different Sonos device."""
    if len(args) < 3:
        return "Error: speaker_name required"
    speaker_name = args[2]
    try:
        sonos_actions.set_master(speaker_name)
        return f"Successfully changed master speaker to {speaker_name}"
    except Exception as e:
        return handle_error(e, "set_master_speaker")


# Music Search Tools

@tool("search_for_track")
def search_for_track(args):
    """Search for music tracks by title, artist, or both."""
    if len(args) < 3:
        return "Error: query required"
    query = args[2]
    try:
        return sonos_actions.search_for_track(query)
    except Exception as e:
        return handle_error(e, "search_for_track")


@tool("search_for_album")
def search_for_album(args):
    """Search for music albums by title or artist."""
    if len(args) < 3:
        return "Error: query required"
    query = args[2]
    try:
        return sonos_actions.search_for_album(query)
    except Exception as e:
        return handle_error(e, "search_for_album")


# Queue Management Tools

@tool("list_queue")
def list_queue(args):
    """Display the current Sonos queue showing all queued tracks."""
    try:
        result = sonos_actions.list_queue()
        if isinstance(result, list):
            # Format as numbered list
            if not result:
                return "Queue is empty"
            output = []
            for i, track in enumerate(result, 1):
                title = track.get('title', 'Unknown')
                artist = track.get('artist', 'Unknown')
                album = track.get('album', 'Unknown')
                output.append(f"{i}. {title} - {artist} - {album}")
            return "\n".join(output)
        return str(result)
    except Exception as e:
        return handle_error(e, "list_queue")


@tool("add_track_to_queue")
def add_track_to_queue(args):
    """Add a track from search results to the queue by position number."""
    if len(args) < 3:
        return "Error: position required"
    try:
        position = int(args[2])
        result = sonos_actions.add_track_to_queue(position)
        return result if result else f"Added track {position} to queue"
    except ValueError:
        return "Error: position must be an integer"
    except Exception as e:
        return handle_error(e, "add_track_to_queue")


@tool("add_album_to_queue")
def add_album_to_queue(args):
    """Add an album from search results to the queue by position number."""
    if len(args) < 3:
        return "Error: position required"
    try:
        position = int(args[2])
        result = sonos_actions.add_album_to_queue(position)
        return result if result else f"Added album {position} to queue"
    except ValueError:
        return "Error: position must be an integer"
    except Exception as e:
        return handle_error(e, "add_album_to_queue")


@tool("clear_queue")
def clear_queue(args):
    """Clear all tracks from the current queue."""
    try:
        sonos_actions.clear_queue()
        return "Queue cleared"
    except Exception as e:
        return handle_error(e, "clear_queue")


@tool("remove_from_queue")
def remove_from_queue(args):
    """Remove a track from the queue by its position number."""
    if len(args) < 3:
        return "Error: position required"
    try:
        position = int(args[2])
        result = sonos_actions.remove_from_queue(position)
        return result if result else f"Removed track {position} from queue"
    except ValueError:
        return "Error: position must be an integer"
    except Exception as e:
        return handle_error(e, "remove_from_queue")


@tool("play_from_queue")
def play_from_queue(args):
    """Play a track from the queue by its position number (1-indexed)."""
    if len(args) < 3:
        return "Error: position required"
    try:
        position = int(args[2])

        # Validate position is positive
        if position < 1:
            return "Error: position must be a positive number (1 or greater)"

        # Get queue to validate position
        queue = sonos_actions.list_queue()
        if position > len(queue):
            return f"Error: position {position} is out of range. Queue has {len(queue)} tracks."

        # Convert from 1-indexed (user-friendly) to 0-indexed (SoCo internal)
        result = sonos_actions.play_from_queue(position - 1)
        return result if result else f"Now playing track {position} from queue"
    except ValueError:
        return "Error: position must be an integer"
    except Exception as e:
        return handle_error(e, "play_from_queue")


# Playback Control Tools

@tool("current_track")
def current_track(args):
    """Get information about what's currently playing."""
    try:
        result = sonos_actions.current_track_info(text=True)
        return result if result else "No track currently playing"
    except Exception as e:
        return handle_error(e, "current_track")


@tool("play_pause")
def play_pause(args):
    """Toggle play/pause of the current track."""
    try:
        result = sonos_actions.play_pause()
        return result if result else "Toggled play/pause"
    except Exception as e:
        return handle_error(e, "play_pause")


@tool("next_track")
def next_track(args):
    """Skip to the next track in the queue."""
    try:
        result = sonos_actions.playback('next')
        return result if result else "Playing next track"
    except Exception as e:
        return handle_error(e, "next_track")


# Volume Control Tools

@tool("turn_volume")
def turn_volume(args):
    """Adjust volume up or down by 10."""
    if len(args) < 3:
        return "Error: direction required (louder/quieter)"
    direction = args[2].lower()
    if direction not in ['louder', 'quieter']:
        return "Error: direction must be 'louder' or 'quieter'"
    try:
        result = sonos_actions.turn_volume(direction)
        return result if result else f"Volume adjusted {direction}"
    except Exception as e:
        return handle_error(e, "turn_volume")


@tool("set_volume")
def set_volume(args):
    """Set the absolute volume level (0-100)."""
    if len(args) < 3:
        return "Error: level required (0-100)"
    try:
        level = int(args[2])
        if not 0 <= level <= 100:
            return "Error: level must be between 0 and 100"
        result = sonos_actions.set_volume(level)
        return result if result else f"Volume set to {level}"
    except ValueError:
        return "Error: level must be an integer"
    except Exception as e:
        return handle_error(e, "set_volume")


@tool("mute")
def mute(args):
    """Mute or unmute all speakers in the group."""
    if len(args) < 3:
        return "Error: muted state required (true/false)"
    muted_str = args[2].lower()
    if muted_str not in ['true', 'false']:
        return "Error: muted must be 'true' or 'false'"
    muted = muted_str == 'true'
    try:
        result = sonos_actions.mute(muted)
        status = "Muted" if muted else "Unmuted"
        return result if result else status
    except Exception as e:
        return handle_error(e, "mute")


# Playlist Management Tools

@tool("list_playlists")
def list_playlists(args):
    """List all available local playlists."""
    try:
        result = sonos_actions.list_playlists()
        return result if result else "No playlists found"
    except Exception as e:
        return handle_error(e, "list_playlists")


@tool("add_to_playlist_from_queue")
def add_to_playlist_from_queue(args):
    """Add a track from the queue to a playlist."""
    if len(args) < 4:
        return "Error: playlist and position required"
    playlist = args[2]
    try:
        position = int(args[3])
        result = sonos_actions.add_to_playlist_from_queue(playlist, position)
        return result if result else f"Added track {position} to playlist {playlist}"
    except ValueError:
        return "Error: position must be an integer"
    except Exception as e:
        return handle_error(e, "add_to_playlist_from_queue")


@tool("add_to_playlist_from_search")
def add_to_playlist_from_search(args):
    """Add a track from search results to a playlist."""
    if len(args) < 4:
        return "Error: playlist and position required"
    playlist = args[2]
    try:
        position = int(args[3])
        result = sonos_actions.add_to_playlist_from_search(playlist, position)
        return result if result else f"Added search result {position} to playlist {playlist}"
    except ValueError:
        return "Error: position must be an integer"
    except Exception as e:
        return handle_error(e, "add_to_playlist_from_search")


@tool("add_playlist_to_queue")
def add_playlist_to_queue(args):
    """Load a playlist to the queue."""
    if len(args) < 3:
        return "Error: playlist name required"
    playlist = args[2]
    # Check for optional shuffle parameter
    shuffle = False
    if len(args) >= 4:
        shuffle_str = args[3].lower()
        if shuffle_str in ['true', 'false']:
            shuffle = shuffle_str == 'true'
        else:
            return "Error: shuffle must be 'true' or 'false'"
    try:
        result = sonos_actions.add_playlist_to_queue(playlist, shuffle)
        shuffle_msg = " (shuffled)" if shuffle else ""
        return result if result else f"Added playlist {playlist} to queue{shuffle_msg}"
    except Exception as e:
        return handle_error(e, "add_playlist_to_queue")


@tool("list_playlist_tracks")
def list_playlist_tracks(args):
    """Display all tracks in a saved playlist."""
    if len(args) < 3:
        return "Error: playlist name required"
    playlist = args[2]
    try:
        # Read playlist file directly
        playlist_path = Path.home() / ".sonos" / "playlists" / f"{playlist}.json"
        if not playlist_path.exists():
            return f"Playlist '{playlist}' not found"

        with open(playlist_path) as f:
            tracks = json.load(f)

        if not tracks:
            return f"Playlist '{playlist}' is empty"

        output = [f"Playlist '{playlist}' ({len(tracks)} tracks):"]
        for i, track in enumerate(tracks, 1):
            title = track.get('title', 'Unknown')
            artist = track.get('artist', 'Unknown')
            album = track.get('album', 'Unknown')
            output.append(f"{i}. {title} - {artist} - {album}")
        return "\n".join(output)
    except Exception as e:
        return handle_error(e, "list_playlist_tracks")


@tool("remove_track_from_playlist")
def remove_track_from_playlist(args):
    """Remove a track from a playlist by position."""
    if len(args) < 4:
        return "Error: playlist and position required"
    playlist = args[2]
    try:
        position = int(args[3])
        # Read, modify, write playlist
        playlist_path = Path.home() / ".sonos" / "playlists" / f"{playlist}.json"
        if not playlist_path.exists():
            return f"Playlist '{playlist}' not found"

        with open(playlist_path) as f:
            tracks = json.load(f)

        if position < 1 or position > len(tracks):
            return f"Error: position must be between 1 and {len(tracks)}"

        removed = tracks.pop(position - 1)

        with open(playlist_path, 'w') as f:
            json.dump(tracks, f, indent=2)

        title = removed.get('title', 'Unknown')
        return f"Removed '{title}' from playlist {playlist}"
    except ValueError:
        return "Error: position must be an integer"
    except Exception as e:
        return handle_error(e, "remove_track_from_playlist")


@tool("list_native_sonos_playlists")
def list_native_sonos_playlists(args):
    """List all native Sonos playlists stored on the Sonos system."""
    try:
        result = sonos_actions.get_native_sonos_playlists()
        return result if result else "No native Sonos playlists found"
    except Exception as e:
        return handle_error(e, "list_native_sonos_playlists")


@tool("create_native_sonos_playlist_from_local")
def create_native_sonos_playlist_from_local(args):
    """Create a native Sonos playlist from a local playlist file."""
    if len(args) < 3:
        return "Error: local_playlist name required"
    local_playlist = args[2]
    native_playlist_name = args[3] if len(args) >= 4 else None
    try:
        result = sonos_actions.create_native_playlist_from_local(
            local_playlist, native_playlist_name
        )
        return result if result else f"Created native Sonos playlist from {local_playlist}"
    except Exception as e:
        return handle_error(e, "create_native_sonos_playlist_from_local")


def main():
    """Main dispatcher entry point."""
    if len(sys.argv) < 2:
        print("Usage: sonos_tool.py <tool_name> [args...]", file=sys.stderr)
        print(f"\nAvailable tools ({len(TOOLS)}):", file=sys.stderr)
        for tool_name in sorted(TOOLS.keys()):
            print(f"  {tool_name}", file=sys.stderr)
        sys.exit(1)

    tool_name = sys.argv[1]

    if tool_name not in TOOLS:
        print(f"Error: Unknown tool '{tool_name}'", file=sys.stderr)
        print(f"\nAvailable tools ({len(TOOLS)}):", file=sys.stderr)
        for name in sorted(TOOLS.keys()):
            print(f"  {name}", file=sys.stderr)
        sys.exit(1)

    # Initialize speaker (except for get_master_speaker which checks connection)
    if tool_name != "get_master_speaker":
        initialize_speaker()

    # Execute tool
    try:
        result = TOOLS[tool_name](sys.argv)
        print(result)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
