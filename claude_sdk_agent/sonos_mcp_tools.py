"""
Sonos MCP tools for Claude Agent SDK.
Defines custom tools using the @tool decorator for controlling Sonos speakers.
"""

import subprocess
from typing import Any, Dict
from claude_agent_sdk import tool, create_sdk_mcp_server


def run_sonos_command(command: str, *args: str) -> str:
    """
    Execute a sonos CLI command and return the output.

    Args:
        command: The sonos subcommand (e.g., 'search-for-track', 'add-track-to-queue')
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


# Define all Sonos tools using the @tool decorator

@tool(
    "search_for_track",
    "Search for music tracks by title, artist, or both. Returns a numbered list of matching tracks.",
    {"query": str}
)
async def search_for_track(args: Dict[str, Any]) -> Dict[str, Any]:
    """Search for tracks matching the query."""
    result = run_sonos_command('search-for-track', args['query'])
    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "search_for_album",
    "Search for music albums by title or artist. Returns a numbered list of matching albums.",
    {"query": str}
)
async def search_for_album(args: Dict[str, Any]) -> Dict[str, Any]:
    """Search for albums matching the query."""
    result = run_sonos_command('search-for-album', args['query'])
    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "add_track_to_queue",
    "Select a track from search results by its number and add it to the Sonos queue.",
    {"position": int}
)
async def add_track_to_queue(args: Dict[str, Any]) -> Dict[str, Any]:
    """Select a track from previous search results and add to queue."""
    result = run_sonos_command('add-track-to-queue', str(args['position']))
    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "add_album_to_queue",
    "Select an album from search results by its number and add it to the Sonos queue.",
    {"position": int}
)
async def add_album_to_queue(args: Dict[str, Any]) -> Dict[str, Any]:
    """Select an album from previous search results and add to queue."""
    result = run_sonos_command('add-album-to-queue', str(args['position']))
    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "add_to_playlist_from_queue",
    "Select a track from the Sonos queue by its number and add it to the specified playlist.",
    {"playlist": str, "position": int}
)
async def add_to_playlist_from_queue(args: Dict[str, Any]) -> Dict[str, Any]:
    """Add a track from the queue to a playlist."""
    result = run_sonos_command(
        'add-to-playlist-from-queue',
        args['playlist'],
        str(args['position'])
    )
    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "add_to_playlist_from_search",
    "Select a track from search by its number and add it to the specified playlist.",
    {"playlist": str, "position": int}
)
async def add_to_playlist_from_search(args: Dict[str, Any]) -> Dict[str, Any]:
    """Add a track from search results to a playlist."""
    result = run_sonos_command(
        'add-to-playlist-from-search',
        args['playlist'],
        str(args['position'])
    )
    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "add_playlist_to_queue",
    "Add a named playlist to the Sonos queue.",
    {"playlist": str}
)
async def add_playlist_to_queue(args: Dict[str, Any]) -> Dict[str, Any]:
    """Add an entire playlist to the queue."""
    result = run_sonos_command('add-playlist-to-queue', args['playlist'])
    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "play_from_queue",
    "Play a track by its number in the Sonos queue.",
    {"position": int}
)
async def play_from_queue(args: Dict[str, Any]) -> Dict[str, Any]:
    """Play a specific track from the queue."""
    result = run_sonos_command('play-from-queue', str(args['position']))
    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "current_track",
    "Get information about what's currently playing on Sonos.",
    {}
)
async def current_track(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get current track information."""
    result = run_sonos_command('what')
    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "list_queue",
    "Display the current Sonos queue showing all queued tracks.",
    {}
)
async def list_queue(args: Dict[str, Any]) -> Dict[str, Any]:
    """Show the current queue."""
    result = run_sonos_command('list-queue')
    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "play_pause",
    "Toggle play/pause of the current track.",
    {}
)
async def play_pause(args: Dict[str, Any]) -> Dict[str, Any]:
    """Toggle play/pause."""
    result = run_sonos_command('play-pause')
    return {
        "content": [{
            "type": "text",
            "text": result if result else "Toggled play/pause"
        }]
    }


@tool(
    "next_track",
    "Skip to the next track in the queue.",
    {}
)
async def next_track(args: Dict[str, Any]) -> Dict[str, Any]:
    """Skip to next track."""
    result = run_sonos_command('next')
    return {
        "content": [{
            "type": "text",
            "text": result if result else "Skipped to next track"
        }]
    }


@tool(
    "clear_queue",
    "Clear all tracks from the current queue.",
    {}
)
async def clear_queue(args: Dict[str, Any]) -> Dict[str, Any]:
    """Clear the queue."""
    result = run_sonos_command('clear-queue')
    return {
        "content": [{
            "type": "text",
            "text": result if result else "Queue cleared"
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
            clear_queue
        ]
    )
