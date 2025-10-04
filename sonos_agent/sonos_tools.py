"""
Sonos CLI tool wrappers for Claude SDK agent.
These functions wrap the existing sonos CLI commands for use as Claude tools.
"""

import subprocess
import json
from typing import Dict, Any, List

def run_sonos_command(command: str, *args: str) -> str:
    """
    Execute a sonos CLI command and return the output.

    Args:
        command: The sonos subcommand (e.g., 'searchtrack', 'select')
        *args: Additional arguments for the command

    Returns:
        Command output as string

    Raises:
        Exception if command fails
    """
    cmd = ['sonos', command] + list(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_msg = f"Sonos command failed: {' '.join(cmd)}\nError: {e.stderr}"
        raise Exception(error_msg)

def search_for_track(query: str) -> str:
    """
    Search for tracks matching the query.

    Args:
        query: Search term (e.g., "harvest by neil young")

    Returns:
        Formatted list of tracks with numbers for selection
    """
    return run_sonos_command('search-for-track', query)

def search_for_album(query: str) -> str:
    """
    Search for albums matching the query.

    Args:
        query: Search term (e.g., "harvest by neil young")

    Returns:
        Formatted list of album with numbers for selection
    """
    return run_sonos_command('search-for-album', query)

def add_track_to_queue(position: int) -> str:
    """
    Select a track from the previous search results and add it to queue.

    Args:
        position: The number of the track to select (1-based)

    Returns:
        Confirmation message
    """
    return run_sonos_command('add-track-to-queue', str(position))

def add_album_to_queue(position: int) -> str:
    """
    Select an album from the previous search results and add it to queue.

    Args:
        position: The number of the album to select (1-based)

    Returns:
        Confirmation message
    """
    return run_sonos_command('add-album-to-queue', str(position))

def add_to_playlist_from_queue(playlist: str, position: int) -> str:
    """
    Select a track from the queue and add it to the specified playlist.

    Args:
        playlist: The name of the playlist
        position: The number of the album to select (1-based)

    Returns:
        Confirmation message
    """
    return run_sonos_command('add-to-playlist-from-queue', playlist, str(position))

def add_to_playlist_from_search(playlist: str, position: int) -> str:
    """
    Select a track from the most recent search and add it to the specified playlist.

    Args:
        playlist: The name of the playlist
        position: The number of the album to select (1-based)

    Returns:
        Confirmation message
    """
    return run_sonos_command('add-to-playlist-from-search', playlist, str(position))

def add_playlist_to_queue(playlist: str) -> str:
    """
    Search for albums matching the query.

    Args:
        query: The name of the playlist

    Returns:
        Formatted list of album with numbers for selection
    """
    return run_sonos_command('add-playlist-to-queue', playlist)

def current_track() -> str:
    """
    Get information about the currently playing track.

    Returns:
        Current track artist, title, and album information
    """
    return run_sonos_command('what')

def show_queue() -> str:
    """
    Show the current Sonos queue.

    Returns:
        Formatted list of tracks in the queue
    """
    return run_sonos_command('show-queue')

def play_pause() -> str:
    """
    Toggle play/pause of the current track.

    Returns:
        Status message
    """
    return run_sonos_command('play-pause')

def next_track() -> str:
    """
    Skip to the next track.

    Returns:
        Status message
    """
    return run_sonos_command('next')

def clear_queue() -> str:
    """
    Clear the current queue.

    Returns:
        Confirmation message
    """
    return run_sonos_command('clear-queue')

def play_from_queue(position: int) -> str:
    """
    Play a specific track from the queue by its position.

    Args:
        position: The position of the track in the queue (1-based)

    Returns:
        Confirmation message
    """
    return run_sonos_command('play-from-queue', str(position))

# Tool definitions for Claude SDK
SONOS_TOOLS = [
    {
        "name": "search_for_track",
        "description": "Search for music tracks by title, artist, or both. Returns a numbered list of matching tracks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for tracks (e.g., 'harvest by neil young', 'hotel california', 'beatles')"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "add_track_to_queue",
        "description": "Select a track from search results by its number and add it to the Sonos queue.",
        "input_schema": {
            "type": "object",
            "properties": {
                "position": {
                    "type": "integer",
                    "description": "The number of the track to select from the search results (1-based)"
                }
            },
            "required": ["position"]
        }
    },
    {
        "name": "add_album_to_queue",
        "description": "Select an album from search results by its number and add it to the Sonos queue.",
        "input_schema": {
            "type": "object",
            "properties": {
                "position": {
                    "type": "integer",
                    "description": "The number of the album to select from the search results (1-based)"
                }
            },
            "required": ["position"]
        }
    },
    {
        "name": "add_to_playlist_from_queue",
        "description": "Select a track from the Sonos queue by its number and add it to the specified playlist.",
        "input_schema": {
            "type": "object",
            "properties": {
                "playlist": {
                    "type": "string",
                    "description": "The name of the playlist to add the track to"
                },
                "position": {
                    "type": "integer",
                    "description": "The number of the track to select from the queue (1-based)"
                }
            },
            "required": ["playlist", "position"]
        }
    },
    {
        "name": "add_to_playlist_from_search",
        "description": "Select a track from search by its number and add it to the specified playlist.",
        "input_schema": {
            "type": "object",
            "properties": {
                "playlist": {
                    "type": "string",
                    "description": "The name of the playlist to add the track to"
                },
                "position": {
                    "type": "integer",
                    "description": "The number of the track to select from the search results (1-based)"
                }
            },
            "required": ["playlist", "position"]
        }
    },
    {
        "name": "add_playlist_to_queue",
        "description": "Add a named playlist to the Sonos queue.",
        "input_schema": {
            "type": "object",
            "properties": {
                "playlist": {
                    "type": "string",
                    "description": "The name of the playlist to add to the queue"
                }
            },
            "required": ["playlist"]
        }
    },
    {
        "name": "play_from_queue",
        "description": "Play a track by its number in the Sonos queue.",
        "input_schema": {
            "type": "object",
            "properties": {
                "position": {
                    "type": "integer",
                    "description": "The number of the track in the Sonos queue (1-based)"
                }
            },
            "required": ["position"]
        }
    },
    {
        "name": "current_track",
        "description": "Get information about what's currently playing on Sonos.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "show_queue",
        "description": "Display the current Sonos queue showing all queued tracks.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "play_pause",
        "description": "Toggle play/pause of the current track.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "next_track",
        "description": "Skip to the next track in the queue.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "clear_queue",
        "description": "Clear all tracks from the current queue.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "search_for_album",
        "description": "Search for music albums by title or artist. Returns a numbered list of matching albums.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for albums (e.g., 'harvest neil young', 'abbey road beatles')"
                }
            },
            "required": ["query"]
        }
    }
]

def get_tool_function(name: str):
    """Get the actual function for a tool by name."""
    tool_functions = {
        'search_for_track': search_for_track,
        'search_for_album': search_for_album,
        'add_track_to_queue': add_track_to_queue,
        'add_album_to_queue': add_album_to_queue,
        'add_to_playlist_from_queue': add_to_playlist_from_queue,
        'add_to_playlist_from_search': add_to_playlist_from_search,
        'add_playlist_to_queue': add_playlist_to_queue,
        'current_track': current_track,
        'show_queue': show_queue,
        'play_pause': play_pause,
        'next_track': next_track,
        'clear_queue': clear_queue,
        'play_from_queue': play_from_queue
    }
    return tool_functions.get(name)
