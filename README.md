# An mcp and agent to interact with Sonos speakers

The sonos mcp utilizaes the SoCo python package. The mcp tools include:  

### Speaker management
- get_master_speaker
- set_master_speaker
### Music search
- search_for_track
- search_for_album
### Queue management
- add_track_to_queue
- add_album_to_queue
- list_queue
- clear_queue
- play_from_queue
### Playback control
- current_track
- play_pause
- next_track
### Playlist management
- add_to_playlist_from_queue
- add_to_playlist_from_search
- add_playlist_to_queue
- list_playlist_tracks
- remove_track_from_playlist

There is an agent based on the Claude Agent SDK that uses the sonos mcp to interact with the sonos system.

With verbose mode you can see the tool calls that the agent is making.  For example:

🎵 You: What's in playlist favorites
🤖 Assistant: 🔧 [TOOL] list_playlist_tracks(playlist='favorites')

Here's what's in your **favorites** - 8 tracks total:

1. **Fixing Her Hair** - Ani DiFranco (from *Imperfectly*)
2. **The Breeze / My Baby Cries** - Bill Callahan (from *Loving Takes This Course - a Tribute to the Songs of Kath Bloom*)
3. **Making Pies** - Patty Griffin (from *1000 Kisses*)
4. **Sweet Surrender** - Sarah McLachlan (from *Surfacing*)
5. **Patient Zero** - Aimee Mann (from *Mental Illness*)
6. **Thrasher** - Neil Young & Crazy Horse (from *Rust Never Sleeps*)
7. **Runes (Dedicated To The Unknown)** - Keith Jarrett (from *Arbour Zena*)
8. **Love in Mind (Live)** - Neil Young (from *Time Fades Away*)

That's a really nice mix! You've got some great singer-songwriters (Ani, Patty Griffin, Aimee Mann), a beautiful live Neil Young track, and even some Keith Jarrett jazz. Would you like me to add this playlist to your queue and start playing it?

🎵 You: Can you play Love in Mind from that playlist?   
🤖 Assistant: 🔧 [TOOL] add_playlist_to_queue(playlist='favorites')   
🔧 [TOOL] list_queue()   
🔧 [TOOL] play_from_queue(position=19)   
🔧 [TOOL] current_track()   

Perfect! I've started playing **Love in Mind (Live at Royce Hall, Los Angeles, California, 1/30/1971)** by Neil Young from the *Time Fades Away* album.
This is such a beautiful live track - one of Neil's most vulnerable performances. The *Time Fades Away* album is legendary for capturing that raw, emotionally intense period of his 1973 tour. Enjoy!

Another example:

🎵 You: Can you find some live versions of songs from Neil Young, Patty Griffin and Bruce Springsteen and add them to the queue?   
🤖 Assistant: 🔧 [TOOL] search_for_track(query='Neil Young live')   
🔧 [TOOL] add_track_to_queue(position=2) [*Note: the positions are the position of the chosen track in the search results*]   
🔧 [TOOL] add_track_to_queue(position=5)   
🔧 [TOOL] search_for_track(query='Patty Griffin live')   
🔧 [TOOL] add_track_to_queue(position=7)   
🔧 [TOOL] add_track_to_queue(position=1)   
🔧 [TOOL] search_for_track(query='Bruce Springsteen live')   
🔧 [TOOL] add_track_to_queue(position=5)   
🔧 [TOOL] add_track_to_queue(position=11)   
🔧 [TOOL] list_queue()   

I'll find some great live tracks from Neil Young, Patty Griffin, and Bruce Springsteen and add them to your queue!  Perfect! I've added 6 great live tracks to your queue from all three artists:

**Neil Young:**
- **Like a Hurricane (Live)** from *Live Rust* - One of his most iconic live performances with that extended guitar solo
- **Old Man (Live)** from *Young Shakespeare* - A beautiful acoustic version

**Patty Griffin:**
- **Up To The Mountain (MLK Song)** from *Live from the Artists Den* - Her powerful tribute to Martin Luther King Jr.
- **Burgundy Shoes** from *Live from the Artists Den* - A gorgeous live performance

**Bruce Springsteen:**
- **The Promised Land (Live)** from the '84 tour - Classic E Street Band energy from the Born in the U.S.A. era
- **Atlantic City (Live)** from the '99 Reunion Tour - A more stripped-down, haunting version of this Nebraska classic

These tracks are now at the end of your queue (positions 20-25). Would you like me to start playing them now, or are you happy with what's currently playing?

**Note:** You can use instructions in the system prompt to guide how wordy and sycophantic/enyhusiastic the agent will be.  For the moment, I am enjoying its commentary and enthusiasm but you have control over that.

