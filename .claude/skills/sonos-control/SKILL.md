---
name: sonos-control
description: Control Sonos speakers through MCP tools - search and play music, manage queue and playlists, adjust volume. Use when users request music playback, mention artists/songs/albums, want to control Sonos speakers, manage playlists, or ask about what's playing.
---

# Sonos Control

## Overview

This skill provides comprehensive control over Sonos speaker systems through MCP tools. Use it to search for and play music, manage playback queues and playlists, control volume, and switch between speakers. The skill handles both simple requests ("play some Neil Young") and complex multi-step workflows ("create a mix of 5 tracks from these artists").

## Core Principle: Multi-Step Workflows

Most music requests require multiple tool calls in sequence. Execute workflows automatically without asking permission at each step - just complete the workflow and confirm the result.

**Critical Rule:** Search results are ephemeral. After using `search_for_track` or `search_for_album`, immediately select and add desired tracks/albums to the queue before executing another search, as each new search clears previous results.

## Available MCP Tools

### Speaker Management
- `sonos:get_master_speaker` - Get current active speaker name
- `sonos:set_master_speaker` - Switch to a different speaker (e.g., "Bedroom", "Kitchen")

### Search and Selection
- `sonos:search_for_track` - Search by track title, artist, album (e.g., "Heart of Gold Neil Young")
- `sonos:search_for_album` - Search by album title and artist (e.g., "Harvest Neil Young")
- `sonos:add_track_to_queue` - Add track from search results by position (1-based)
- `sonos:add_album_to_queue` - Add album from search results by position (1-based)

### Queue Management
- `sonos:list_queue` - View all queued tracks
- `sonos:clear_queue` - Remove all tracks from queue
- `sonos:play_from_queue` - Play track at specific queue position (1-based)

### Playback Control
- `sonos:current_track` - Get information about currently playing track
- `sonos:play_pause` - Toggle play/pause
- `sonos:next_track` - Skip to next track

### Volume Control
- `sonos:turn_volume` - Adjust volume by 10 ("louder" or "quieter")
- `sonos:set_volume` - Set absolute volume (0-100)
- `sonos:mute` - Mute or unmute (True/False)

### Playlist Management
- `sonos:list_playlists` - Display all saved playlists
- `sonos:list_playlist_tracks` - Show tracks in a specific playlist
- `sonos:add_to_playlist_from_queue` - Add queue track to playlist by position
- `sonos:add_to_playlist_from_search` - Add search result to playlist by position
- `sonos:add_playlist_to_queue` - Load entire playlist into queue
- `sonos:remove_track_from_playlist` - Remove track from playlist by position

## Basic Workflow: Play a Track or Album

To play a specific track or album:

1. **Search** - Use `sonos:search_for_track` or `sonos:search_for_album`
2. **Select** - Use `sonos:add_track_to_queue` or `sonos:add_album_to_queue` with position number
3. **Find Position** - Use `sonos:list_queue` to see where track(s) were added
4. **Play** - Use `sonos:play_from_queue` with the position from step 3
5. **Verify** - Use `sonos:current_track` to confirm correct track is playing

**Example:** User says "play Like a Hurricane by Neil Young"
```
1. sonos:search_for_track "Like a Hurricane Neil Young"
2. sonos:add_track_to_queue 1  (select best match)
3. sonos:list_queue  (find it was added at position 15)
4. sonos:play_from_queue 15
5. sonos:current_track  (confirm)
```

## Advanced Workflows

### Creating Custom Mixes

To build a custom mix from multiple artists:

1. **For each artist:** Execute search → select → add cycle
2. **Between searches:** Ensure previous track is added to queue before next search
3. **Play first track** when all selections complete
4. **Verify** the queue contains all desired tracks

**Example:** User says "play a mix of Springsteen, Jackson Browne, and Patty Griffin"
```
1. sonos:search_for_track "Born to Run Springsteen"
2. sonos:add_track_to_queue 1
3. sonos:search_for_track "Running on Empty Jackson Browne"
4. sonos:add_track_to_queue 1
5. sonos:search_for_track "Let Him Fly Patty Griffin"
6. sonos:add_track_to_queue 1
7. sonos:list_queue (verify all added)
8. sonos:play_from_queue 1 (start first track)
```

### Finding Live Performances

To find live tracks or albums:

1. **Include "live" or "unplugged" in search queries**
2. **Look for venue names** in search results: "Massey Hall", "Nashville", "The Troubadour", "Red Rocks", "The Fillmore", "The Ryman"
3. **Check album titles** for indicators: "Live at", "Unplugged", "In Concert"

**Example:** User says "play 5 live tracks from Patty Griffin"
```
1. sonos:search_for_track "Patty Griffin live"
2. Review results for venue names or "live" indicators
3. sonos:add_track_to_queue 1
4. sonos:add_track_to_queue 3
5. sonos:add_track_to_queue 5
6. sonos:add_track_to_queue 7
7. sonos:add_track_to_queue 9
8. sonos:play_from_queue 1
```

### Multi-Room Control

To play music in a specific room:

1. **Switch speaker first** - Use `sonos:set_master_speaker` with room name
2. **Verify switch** - Check response confirms speaker change
3. **Continue with normal workflow** - Search, add, play as usual

**Example:** User says "play some Neil Young in the bedroom"
```
1. sonos:set_master_speaker "Bedroom"
2. sonos:search_for_track "Neil Young"
3. sonos:add_track_to_queue 1
4. sonos:play_from_queue 1
```

## Playlist Workflows

### Adding Tracks to Playlists

**From queue:**
1. Use `sonos:list_queue` to find track position
2. Use `sonos:add_to_playlist_from_queue` with playlist name and position

**From search:**
1. Use `sonos:search_for_track` to find track
2. Use `sonos:add_to_playlist_from_search` with playlist name and position

**Example:** User says "add the current track to my Chill Vibes playlist"
```
1. sonos:current_track (get what's playing)
2. sonos:list_queue (find its position)
3. sonos:add_to_playlist_from_queue "Chill Vibes" <position>
```

### Playing Playlists

To play a saved playlist:
1. Use `sonos:add_playlist_to_queue` to load all tracks
2. Use `sonos:play_from_queue 1` to start playing

## Common Request Patterns

### Simple Requests
- "What's playing?" → `sonos:current_track`
- "Show me the queue" → `sonos:list_queue`
- "Turn it up" → `sonos:turn_volume "louder"`
- "Set volume to 50" → `sonos:set_volume 50`
- "Mute" → `sonos:mute True`
- "Next song" → `sonos:next_track`
- "Pause" → `sonos:play_pause`
- "What playlists do I have?" → `sonos:list_playlists`

### Complex Requests
- "Play [specific track]" → Execute Basic Workflow
- "Play [number] tracks by [artist]" → Execute Advanced Workflow with multiple searches
- "Create a mix of [artists]" → Execute Custom Mix Workflow
- "Play some [artist] in [room]" → Execute Multi-Room Workflow
- "Add [track] to [playlist]" → Execute Playlist Workflow

## Response Guidelines

### After Completing Workflows

Provide natural, music-focused responses:
- Confirm what's playing
- Share relevant context (album, year, interesting facts)
- Explain selection reasoning for custom mixes
- Mention notable aspects (live performance, rare version, etc.)

### When Making Selections

Use music knowledge to select best matches:
- Prefer original studio versions unless user requests otherwise
- For "live" requests, prioritize well-known live albums
- For deep cuts, select lesser-known but high-quality tracks
- Consider chronology and artist periods when building mixes

### Handling Ambiguity

If search results are unclear:
- Make best judgment based on context
- Select most popular/canonical version
- Only ask for clarification if results are completely ambiguous
- Provide reasoning for selection in response

## Error Handling

### Search Returns No Results
- Try simplified search (fewer keywords)
- Suggest alternative artist/track names
- Offer to search for similar artists or tracks
- Consult `references/search_tips.md` for search strategies

### Queue Issues
- If queue is full, suggest clearing old tracks
- If position is invalid, list queue to find correct position

### Playback Issues
- Verify track is in queue using `sonos:list_queue`
- Confirm correct speaker using `sonos:get_master_speaker`
- Check current status with `sonos:current_track`

## Additional Resources

For detailed search strategies, artist name variations, and mix-building tips, reference the bundled file:
- `references/search_tips.md` - Comprehensive guide for effective music searches
