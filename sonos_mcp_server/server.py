#!/home/slzatz/sonos_mcp/.venv/bin/python3
"""
Standalone Sonos MCP Server
Exposes Sonos control functionality as MCP tools using stdio transport.
"""

import sys
import json
from pathlib import Path
from time import sleep
from mcp.server.fastmcp import FastMCP

# Add parent directory to path to import sonos modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sonos import sonos_actions
from sonos.config import master_speaker

# Initialize FastMCP server
mcp = FastMCP("sonos-mcp-server")


def initialize_speaker(max_retries=10):
    """Initialize Sonos speaker connection with retry logic."""
    for attempt in range(max_retries):
        try:
            speaker = sonos_actions.set_master(master_speaker)
            if speaker:
                print(f"Successfully connected to speaker: {master_speaker}", file=sys.stderr)
                return speaker
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Speaker discovery attempt {attempt + 1}/{max_retries} failed: {e}", file=sys.stderr)
                sleep(1)
            else:
                print(f"ERROR: Failed to connect to speaker '{master_speaker}' after {max_retries} attempts", file=sys.stderr)
                raise
    return None


# Initialize speaker connection on startup
try:
    initialize_speaker()
except Exception as e:
    print(f"WARNING: Could not initialize speaker on startup: {e}", file=sys.stderr)
    print("Speaker initialization will be retried on first tool call", file=sys.stderr)


# Speaker Management Tools

@mcp.tool()
async def get_master_speaker() -> str:
    """Get the currently configured master speaker name."""
    if sonos_actions.master:
        return f"Current master speaker: {sonos_actions.master.player_name}"
    return "No master speaker currently connected"


@mcp.tool()
async def set_master_speaker(speaker_name: str) -> str:
    """
    Change the master speaker to a different Sonos device.

    Args:
        speaker_name: Name of the Sonos speaker to use as master
    """
    try:
        new_master = sonos_actions.set_master(speaker_name)
        if new_master:
            sonos_actions.master = new_master
            return f"Successfully changed master speaker to: {speaker_name}"
        else:
            return f"Failed to find speaker named: {speaker_name}"
    except Exception as e:
        return f"Error changing master speaker: {str(e)}"


# Music Search Tools

@mcp.tool()
async def search_for_track(query: str) -> str:
    """
    Search for music tracks by title, artist, or both.
    Returns a numbered list of matching tracks.

    Args:
        query: Search query (e.g., "Heart of Gold Neil Young")
    """
    try:
        result = sonos_actions.search_for_track(query)
        return result
    except Exception as e:
        return f"Failed to search for track: {str(e)}"


@mcp.tool()
async def search_for_album(query: str) -> str:
    """
    Search for music albums by title or artist.
    Returns a numbered list of matching albums.

    Args:
        query: Search query (e.g., "Harvest Moon" or "Neil Young")
    """
    try:
        result = sonos_actions.search_for_album(query)
        return result
    except Exception as e:
        return f"Failed to search for album: {str(e)}"


# Queue Management Tools

@mcp.tool()
async def add_track_to_queue(position: int) -> str:
    """
    Select a track from search results by its number and add it to the Sonos queue.

    Args:
        position: The number of the track from search results (1-indexed)
    """
    try:
        sonos_actions.add_track_to_queue(position)
        return f"Successfully added track {position} to the queue"
    except Exception as e:
        return f"Failed to add track to queue: {str(e)}"


@mcp.tool()
async def add_album_to_queue(position: int) -> str:
    """
    Select an album from search results by its number and add it to the Sonos queue.

    Args:
        position: The number of the album from search results (1-indexed)
    """
    try:
        sonos_actions.add_album_to_queue(position)
        return f"Successfully added album {position} to the queue"
    except Exception as e:
        return f"Failed to add album to queue: {str(e)}"


@mcp.tool()
async def list_queue() -> str:
    """Display the current Sonos queue showing all queued tracks."""
    try:
        queue = sonos_actions.list_queue()
        if not queue:
            return "The queue is empty"

        # Format the queue into a numbered list
        queue_lines = []
        for num, track in enumerate(queue, start=1):
            title = track.get('title', 'Unknown')
            artist = track.get('artist', 'Unknown')
            album = track.get('album', 'Unknown')
            queue_lines.append(f"{num}. {title} - {artist} - {album}")

        return "\n".join(queue_lines)
    except Exception as e:
        return f"Failed to get queue: {str(e)}"


@mcp.tool()
async def clear_queue() -> str:
    """Clear all tracks from the current queue."""
    try:
        sonos_actions.clear_queue()
        return "Queue cleared"
    except Exception as e:
        return f"Failed to clear queue: {str(e)}"


@mcp.tool()
async def play_from_queue(position: int) -> str:
    """
    Play a track by its number in the Sonos queue.

    Args:
        position: The track number in the queue (1-indexed)
    """
    try:
        # Convert from 1-indexed (user-friendly) to 0-indexed (SoCo internal)
        sonos_actions.play_from_queue(position - 1)
        return f"Now playing track {position} from the queue"
    except Exception as e:
        return f"Failed to play from queue: {str(e)}"


# Playback Control Tools

@mcp.tool()
async def current_track() -> str:
    """Get information about what's currently playing on Sonos."""
    try:
        result = sonos_actions.current_track_info(text=True)
        if result:
            return result
        else:
            return "Nothing appears to be playing"
    except Exception as e:
        return f"Failed to get current track info: {str(e)}"


@mcp.tool()
async def play_pause() -> str:
    """Toggle play/pause of the current track."""
    try:
        sonos_actions.play_pause()
        return "Toggled play/pause"
    except Exception as e:
        return f"Failed to toggle play/pause: {str(e)}"


@mcp.tool()
async def next_track() -> str:
    """Skip to the next track in the queue."""
    try:
        sonos_actions.playback('next')
        return "Skipped to next track"
    except Exception as e:
        return f"Failed to skip track: {str(e)}"


# Volume Control Tools

@mcp.tool()
async def turn_volume(direction: str) -> str:
    """
    Adjust volume up or down by 10 for all speakers in the group.

    Args:
        direction: "louder" to increase volume, "quieter" to decrease volume
    """
    try:
        sonos_actions.turn_volume(direction)
        change = "increased" if direction != "quieter" else "decreased"
        return f"Volume {change} by 10"
    except Exception as e:
        return f"Failed to adjust volume: {str(e)}"


@mcp.tool()
async def set_volume(level: int) -> str:
    """
    Set the absolute volume level for all speakers in the group.

    Args:
        level: Volume level from 0 (muted) to 100 (maximum)
    """
    try:
        if level < 0 or level > 100:
            return "Volume level must be between 0 and 100"
        sonos_actions.set_volume(level)
        return f"Volume set to {level}"
    except Exception as e:
        return f"Failed to set volume: {str(e)}"


@mcp.tool()
async def mute(muted: bool) -> str:
    """
    Mute or unmute all speakers in the group.

    Args:
        muted: True to mute, False to unmute
    """
    try:
        sonos_actions.mute(muted)
        status = "muted" if muted else "unmuted"
        return f"Speakers {status}"
    except Exception as e:
        return f"Failed to change mute status: {str(e)}"


# Playlist Management Tools

@mcp.tool()
async def add_to_playlist_from_queue(playlist: str, position: int) -> str:
    """
    Select a track from the Sonos queue by its number and add it to the specified playlist.

    Args:
        playlist: Name of the playlist to add the track to
        position: The track number in the queue (1-indexed)
    """
    try:
        result = sonos_actions.add_to_playlist_from_queue(playlist, position)
        return result
    except Exception as e:
        return f"Failed to add track from queue to playlist: {str(e)}"


@mcp.tool()
async def add_to_playlist_from_search(playlist: str, position: int) -> str:
    """
    Select a track from search results by its number and add it to the specified playlist.

    Args:
        playlist: Name of the playlist to add the track to
        position: The track number from search results (1-indexed)
    """
    try:
        result = sonos_actions.add_to_playlist_from_search(playlist, position)
        return result
    except Exception as e:
        return f"Failed to add track from search to playlist: {str(e)}"


@mcp.tool()
async def add_playlist_to_queue(playlist: str) -> str:
    """
    Add a named playlist to the Sonos queue.

    Args:
        playlist: Name of the saved playlist
    """
    try:
        result = sonos_actions.add_playlist_to_queue(playlist)
        return result
    except Exception as e:
        return f"Failed to add playlist to queue: {str(e)}"


@mcp.tool()
async def list_playlists() -> str:
    """
    List all available playlists.
    Returns a numbered list of all saved playlists.
    """
    try:
        result = sonos_actions.list_playlists()
        return result
    except Exception as e:
        return f"Failed to list playlists: {str(e)}"


@mcp.tool()
async def list_playlist_tracks(playlist: str) -> str:
    """
    Display all tracks in a saved playlist by name.

    Args:
        playlist: Name of the playlist to display
    """
    try:
        playlist_name = playlist
        file_path = Path.home() / ".sonos" / "playlists" / playlist_name

        if not file_path.is_file():
            return f"Playlist '{playlist_name}' does not exist"

        with file_path.open('r') as file:
            tracks = json.load(file)

        if not tracks:
            return f"Playlist '{playlist_name}' is empty"

        # Format tracks into a numbered list
        track_lines = []
        for num, track in enumerate(tracks, start=1):
            title = track.get('title', 'Unknown')
            artist = track.get('artist', 'Unknown')
            album = track.get('album', 'Unknown')
            track_lines.append(f"{num}. {title} - {artist} - {album}")

        header = f"Playlist '{playlist_name}' ({len(tracks)} tracks):\n"
        return header + "\n".join(track_lines)
    except Exception as e:
        return f"Failed to read playlist: {str(e)}"


@mcp.tool()
async def remove_track_from_playlist(playlist: str, position: int) -> str:
    """
    Remove a track from a saved playlist by its position number.

    Args:
        playlist: Name of the playlist
        position: The track number to remove (1-indexed)
    """
    try:
        playlist_name = playlist
        file_path = Path.home() / ".sonos" / "playlists" / playlist_name

        if not file_path.is_file():
            return f"Playlist '{playlist_name}' does not exist"

        with file_path.open('r') as file:
            tracks = json.load(file)

        if not tracks:
            return f"Playlist '{playlist_name}' is empty"

        # Validate position (1-indexed for user-friendliness)
        if position < 1 or position > len(tracks):
            return f"Position {position} is out of range. Playlist has {len(tracks)} tracks."

        # Remove the track (convert to 0-indexed)
        removed_track = tracks.pop(position - 1)

        # Write updated playlist back to file
        with file_path.open('w') as file:
            json.dump(tracks, file, indent=2)

        title = removed_track.get('title', 'Unknown')
        artist = removed_track.get('artist', 'Unknown')

        return f"Removed track {position}: {title} by {artist} from playlist '{playlist_name}'"
    except Exception as e:
        return f"Failed to remove track from playlist: {str(e)}"


def main():
    """Run the MCP server with stdio transport."""
    print("Starting Sonos MCP Server...", file=sys.stderr)
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()
