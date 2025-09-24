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

def search_track(query: str) -> str:
    """
    Search for tracks matching the query.

    Args:
        query: Search term (e.g., "harvest by neil young")

    Returns:
        Formatted list of tracks with numbers for selection
    """
    return run_sonos_command('searchtrack', query)

def select_track(position: int) -> str:
    """
    Select a track from the previous search results and add to queue.

    Args:
        position: The number of the track to select (1-based)

    Returns:
        Confirmation message
    """
    return run_sonos_command('select', str(position))

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
    return run_sonos_command('showqueue')

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
    return run_sonos_command('clearqueue')

def search_album(query: str) -> str:
    """
    Search for albums matching the query.

    Args:
        query: Album search term

    Returns:
        Formatted list of albums with numbers for selection
    """
    return run_sonos_command('searchalbum', query)

# Tool definitions for Claude SDK
SONOS_TOOLS = [
    {
        "name": "search_track",
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
        "name": "select_track",
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
        "name": "search_album",
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
        'search_track': search_track,
        'select_track': select_track,
        'current_track': current_track,
        'show_queue': show_queue,
        'play_pause': play_pause,
        'next_track': next_track,
        'clear_queue': clear_queue,
        'search_album': search_album
    }
    return tool_functions.get(name)