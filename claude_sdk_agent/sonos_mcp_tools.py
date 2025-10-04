"""
Sonos MCP tools for Claude Agent SDK.
Defines custom tools using the @tool decorator for controlling Sonos speakers.
"""

from typing import Any, Dict
from time import sleep
import json
from pathlib import Path
from claude_agent_sdk import tool, create_sdk_mcp_server

from sonos import sonos_actions
from sonos.config import master_speaker

# Initialize speaker connection with retry logic (SoCo discovery can be flaky)
def initialize_speaker(max_retries=10):
    """Initialize Sonos speaker connection with retry logic."""
    for attempt in range(max_retries):
        try:
            speaker = sonos_actions.set_master(master_speaker)
            if speaker:
                print(f"Successfully connected to speaker: {master_speaker}")
                return speaker
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Speaker discovery attempt {attempt + 1}/{max_retries} failed: {e}")
                sleep(1)
            else:
                print(f"ERROR: Failed to connect to speaker '{master_speaker}' after {max_retries} attempts")
                raise
    return None

sonos_actions.master = initialize_speaker()


# Define all Sonos tools using the @tool decorator

@tool(
    "search_for_track",
    "Search for music tracks by title, artist, or both. Returns a numbered list of matching tracks.",
    {"query": str}
)
async def search_for_track(args: Dict[str, Any]) -> Dict[str, Any]:
    """Search for tracks matching the query."""
    try:
        result = sonos_actions.search_for_track(args['query'])
        return {
            "content": [{
                "type": "text",
                "text": result
            }]
        }
    except Exception as e:
        error_msg = f"Failed to search for track: {str(e)}"
        return {
            "content": [{
                "type": "text",
                "text": error_msg
            }]
        }


@tool(
    "search_for_album",
    "Search for music albums by title or artist. Returns a numbered list of matching albums.",
    {"query": str}
)
async def search_for_album(args: Dict[str, Any]) -> Dict[str, Any]:
    """Search for albums matching the query."""
    try:
        result = sonos_actions.search_for_album(args['query'])
        return {
            "content": [{
                "type": "text",
                "text": result
            }]
        }
    except Exception as e:
        error_msg = f"Failed to search for album: {str(e)}"
        return {
            "content": [{
                "type": "text",
                "text": error_msg
            }]
        }


@tool(
    "add_track_to_queue",
    "Select a track from search results by its number and add it to the Sonos queue.",
    {"position": int}
)
async def add_track_to_queue(args: Dict[str, Any]) -> Dict[str, Any]:
    """Select a track from previous search results and add to queue."""
    try:
        sonos_actions.add_track_to_queue(args['position'])
        return {
            "content": [{
                "type": "text",
                "text": f"Successfully added track {args['position']} to the queue"
            }]
        }
    except Exception as e:
        error_msg = f"Failed to add track to queue: {str(e)}"
        return {
            "content": [{
                "type": "text",
                "text": error_msg
            }]
        }


@tool(
    "add_album_to_queue",
    "Select an album from search results by its number and add it to the Sonos queue.",
    {"position": int}
)
async def add_album_to_queue(args: Dict[str, Any]) -> Dict[str, Any]:
    """Select an album from previous search results and add to queue."""
    try:
        sonos_actions.add_album_to_queue(args['position'])
        return {
            "content": [{
                "type": "text",
                "text": f"Successfully added album {args['position']} to the queue"
            }]
        }
    except Exception as e:
        error_msg = f"Failed to add album to queue: {str(e)}"
        return {
            "content": [{
                "type": "text",
                "text": error_msg
            }]
        }


@tool(
    "add_to_playlist_from_queue",
    "Select a track from the Sonos queue by its number and add it to the specified playlist.",
    {"playlist": str, "position": int}
)
async def add_to_playlist_from_queue(args: Dict[str, Any]) -> Dict[str, Any]:
    """Add a track from the queue to a playlist."""
    try:
        result = sonos_actions.add_to_playlist_from_queue(args['playlist'], args['position'])
        return {
            "content": [{
                "type": "text",
                "text": result
            }]
        }
    except Exception as e:
        error_msg = f"Failed to add track from queue to playlist: {str(e)}"
        return {
            "content": [{
                "type": "text",
                "text": error_msg
            }]
        }


@tool(
    "add_to_playlist_from_search",
    "Select a track from search by its number and add it to the specified playlist.",
    {"playlist": str, "position": int}
)
async def add_to_playlist_from_search(args: Dict[str, Any]) -> Dict[str, Any]:
    """Add a track from search results to a playlist."""
    try:
        result = sonos_actions.add_to_playlist_from_search(args['playlist'], args['position'])
        return {
            "content": [{
                "type": "text",
                "text": result
            }]
        }
    except Exception as e:
        error_msg = f"Failed to add track from search to playlist: {str(e)}"
        return {
            "content": [{
                "type": "text",
                "text": error_msg
            }]
        }


@tool(
    "add_playlist_to_queue",
    "Add a named playlist to the Sonos queue.",
    {"playlist": str}
)
async def add_playlist_to_queue(args: Dict[str, Any]) -> Dict[str, Any]:
    """Add an entire playlist to the queue."""
    try:
        result = sonos_actions.add_playlist_to_queue(args['playlist'])
        return {
            "content": [{
                "type": "text",
                "text": result
            }]
        }
    except Exception as e:
        error_msg = f"Failed to add playlist to queue: {str(e)}"
        return {
            "content": [{
                "type": "text",
                "text": error_msg
            }]
        }


@tool(
    "play_from_queue",
    "Play a track by its number in the Sonos queue.",
    {"position": int}
)
async def play_from_queue(args: Dict[str, Any]) -> Dict[str, Any]:
    """Play a specific track from the queue."""
    try:
        # Convert from 1-indexed (user-friendly) to 0-indexed (SoCo internal)
        sonos_actions.play_from_queue(args['position'] - 1)
        return {
            "content": [{
                "type": "text",
                "text": f"Now playing track {args['position']} from the queue"
            }]
        }
    except Exception as e:
        error_msg = f"Failed to play from queue: {str(e)}"
        return {
            "content": [{
                "type": "text",
                "text": error_msg
            }]
        }


@tool(
    "current_track",
    "Get information about what's currently playing on Sonos.",
    {}
)
async def current_track(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get current track information."""
    try:
        result = sonos_actions.current_track_info(text=True)
        if result:
            return {
                "content": [{
                    "type": "text",
                    "text": result
                }]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": "Nothing appears to be playing"
                }]
            }
    except Exception as e:
        error_msg = f"Failed to get current track info: {str(e)}"
        return {
            "content": [{
                "type": "text",
                "text": error_msg
            }]
        }


@tool(
    "list_queue",
    "Display the current Sonos queue showing all queued tracks.",
    {}
)
async def list_queue(args: Dict[str, Any]) -> Dict[str, Any]:
    """Show the current queue."""
    try:
        queue = sonos_actions.list_queue()
        if not queue:
            return {
                "content": [{
                    "type": "text",
                    "text": "The queue is empty"
                }]
            }

        # Format the queue into a numbered list
        queue_lines = []
        for num, track in enumerate(queue, start=1):
            title = track.get('title', 'Unknown')
            artist = track.get('artist', 'Unknown')
            album = track.get('album', 'Unknown')
            queue_lines.append(f"{num}. {title} - {artist} - {album}")

        return {
            "content": [{
                "type": "text",
                "text": "\n".join(queue_lines)
            }]
        }
    except Exception as e:
        error_msg = f"Failed to get queue: {str(e)}"
        return {
            "content": [{
                "type": "text",
                "text": error_msg
            }]
        }


@tool(
    "play_pause",
    "Toggle play/pause of the current track.",
    {}
)
async def play_pause(args: Dict[str, Any]) -> Dict[str, Any]:
    """Toggle play/pause."""
    try:
        sonos_actions.play_pause()
        return {
            "content": [{
                "type": "text",
                "text": "Toggled play/pause"
            }]
        }
    except Exception as e:
        error_msg = f"Failed to toggle play/pause: {str(e)}"
        return {
            "content": [{
                "type": "text",
                "text": error_msg
            }]
        }


@tool(
    "next_track",
    "Skip to the next track in the queue.",
    {}
)
async def next_track(args: Dict[str, Any]) -> Dict[str, Any]:
    """Skip to next track."""
    try:
        sonos_actions.playback('next')
        return {
            "content": [{
                "type": "text",
                "text": "Skipped to next track"
            }]
        }
    except Exception as e:
        error_msg = f"Failed to skip track: {str(e)}"
        return {
            "content": [{
                "type": "text",
                "text": error_msg
            }]
        }


@tool(
    "clear_queue",
    "Clear all tracks from the current queue.",
    {}
)
async def clear_queue(args: Dict[str, Any]) -> Dict[str, Any]:
    """Clear the queue."""
    try:
        sonos_actions.clear_queue()
        return {
            "content": [{
                "type": "text",
                "text": "Queue cleared"
            }]
        }
    except Exception as e:
        error_msg = f"Failed to clear queue: {str(e)}"
        return {
            "content": [{
                "type": "text",
                "text": error_msg
            }]
        }


@tool(
    "list_playlist_tracks",
    "Display all tracks in a saved playlist by name.",
    {"playlist": str}
)
async def list_playlist_tracks(args: Dict[str, Any]) -> Dict[str, Any]:
    """List all tracks in a saved playlist."""
    try:
        playlist_name = args['playlist']
        file_path = Path.home() / ".sonos" / "playlists" / playlist_name

        if not file_path.is_file():
            return {
                "content": [{
                    "type": "text",
                    "text": f"Playlist '{playlist_name}' does not exist"
                }]
            }

        with file_path.open('r') as file:
            tracks = json.load(file)

        if not tracks:
            return {
                "content": [{
                    "type": "text",
                    "text": f"Playlist '{playlist_name}' is empty"
                }]
            }

        # Format tracks into a numbered list
        track_lines = []
        for num, track in enumerate(tracks, start=1):
            title = track.get('title', 'Unknown')
            artist = track.get('artist', 'Unknown')
            album = track.get('album', 'Unknown')
            track_lines.append(f"{num}. {title} - {artist} - {album}")

        header = f"Playlist '{playlist_name}' ({len(tracks)} tracks):\n"
        return {
            "content": [{
                "type": "text",
                "text": header + "\n".join(track_lines)
            }]
        }
    except Exception as e:
        error_msg = f"Failed to read playlist: {str(e)}"
        return {
            "content": [{
                "type": "text",
                "text": error_msg
            }]
        }


@tool(
    "remove_track_from_playlist",
    "Remove a track from a saved playlist by its position number.",
    {"playlist": str, "position": int}
)
async def remove_track_from_playlist(args: Dict[str, Any]) -> Dict[str, Any]:
    """Remove a track from a saved playlist."""
    try:
        playlist_name = args['playlist']
        position = args['position']
        file_path = Path.home() / ".sonos" / "playlists" / playlist_name

        if not file_path.is_file():
            return {
                "content": [{
                    "type": "text",
                    "text": f"Playlist '{playlist_name}' does not exist"
                }]
            }

        with file_path.open('r') as file:
            tracks = json.load(file)

        if not tracks:
            return {
                "content": [{
                    "type": "text",
                    "text": f"Playlist '{playlist_name}' is empty"
                }]
            }

        # Validate position (1-indexed for user-friendliness)
        if position < 1 or position > len(tracks):
            return {
                "content": [{
                    "type": "text",
                    "text": f"Position {position} is out of range. Playlist has {len(tracks)} tracks."
                }]
            }

        # Remove the track (convert to 0-indexed)
        removed_track = tracks.pop(position - 1)

        # Write updated playlist back to file
        with file_path.open('w') as file:
            json.dump(tracks, file, indent=2)

        title = removed_track.get('title', 'Unknown')
        artist = removed_track.get('artist', 'Unknown')

        return {
            "content": [{
                "type": "text",
                "text": f"Removed track {position}: {title} by {artist} from playlist '{playlist_name}'"
            }]
        }
    except Exception as e:
        error_msg = f"Failed to remove track from playlist: {str(e)}"
        return {
            "content": [{
                "type": "text",
                "text": error_msg
            }]
        }


# Create the MCP server with all tools
def create_sonos_mcp_server():
    """
    Create and return the Sonos MCP server with all tools registered.

    Returns:
        McpSdkServerConfig: MCP server configuration for use with ClaudeAgentOptions
    """
    return create_sdk_mcp_server(
        name="sonos",
        version="1.0.0",
        tools=[
            search_for_track,
            search_for_album,
            add_track_to_queue,
            add_album_to_queue,
            add_to_playlist_from_queue,
            add_to_playlist_from_search,
            add_playlist_to_queue,
            play_from_queue,
            current_track,
            list_queue,
            play_pause,
            next_track,
            clear_queue,
            list_playlist_tracks,
            remove_track_from_playlist
        ]
    )
