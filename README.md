# An mcp and agent to interact with Sonos speakers

The sonos mcp coupled with the sonos_agent allows control of the Sonos system through natural language interactioins with an LLM that leverages the ability of an LLM to use and sequence tools to accomplish a request and also takes advantage of the music-related information that the model was trained on.  The agent utilizes the claude agent sdk and the mcp uses the SoCo python package.

The MCPs available functions are:

### Speaker management
- get_master_speaker
- set_master_speaker
### Volume control
- turn_volume
- set_volume
- mute
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
**Local playlists (stored on filesystem):**
- add_to_playlist_from_queue
- add_to_playlist_from_search
- add_playlist_to_queue
- list_playlists
- list_playlist_tracks
- remove_track_from_playlist

**Native Sonos playlists (stored on Sonos system):**
- list_native_sonos_playlists
- create_native_sonos_playlist_from_local

The sonos agent has access to all the functions (tools) and decides how to use them to accomplish the user's requests.

The agent has a number of optional command line arguments:

- --verbose (-v): show the tool calls the agent is making
- --log (-l): enable logging of interactions and tool calls to the specified log file
- --prompt: run in headless mode using the prompt provided on the command line
- --resume (-r): resume a previous conversation from the session id (recorded to screen and log file)
- --continue-conversation (-c): continue the previous conversation

**Experimental: Interactive TUI Mode**

For multi-track search workflows, an experimental interactive TUI (`sonos_interactive_tui.py`) is available. When used with tmux, it allows the agent to:
- Launch a persistent search interface
- Examine search results before selection
- Build queues interactively with multiple searches
- Choose whether to play tracks immediately or just queue them

This demonstrates a new interaction pattern where AI agents can work with terminal UIs by capturing display state and sending keystrokes through tmux. See `CLAUDE.md` for details.

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

Last example:

🎵 You: can you find some songs from the Drive By Truckers that were written by Jason Isbell and put them on the queue
🤖 Assistant: 🔧 [TOOL] search_for_track(query='Drive-By Truckers Jason Isbell Outfit')
🔧 [TOOL] search_for_track(query='Drive-By Truckers Decoration Day')
🔧 [TOOL] add_track_to_queue(position=1)
...
🔧 [TOOL] list_queue()
I'll search for Drive-By Truckers songs written by Jason Isbell and add them to your queue.Let me search more broadly for Drive-By Truckers tracks:Great! I can see "Decoration Day" and "Outfit" - both Jason Isbell classics. Let me add "Decoration Day" first and then search for more Isbell-penned tracks:Perfect! I've added 5 excellent Drive-By Truckers songs written by Jason Isbell to your queue. Here's what I selected:

1. **Decoration Day** - The powerful title track from their 2003 album, telling a dark story about family feuds and cycles of violence
2. **Outfit** - A deeply personal song based on advice Jason's father gave him, one of his most beloved tracks
3. **Goddamn Lonely Love** - An emotionally raw track from The Dirty South about heartbreak and longing
4. **Danko/Manuel** - A beautiful tribute to The Band's Rick Danko and Richard Manuel, showcasing Isbell's storytelling at its finest
5. **Never Gonna Change** - Another gem from The Dirty South about being stuck in destructive patterns

These tracks are from Jason's time with the band (roughly 2001-2007) and represent some of his best songwriting before he

Another example showing native Sonos playlists:

🎵 You: Can you create a native Sonos playlist from my favorites playlist so I can access it in the Sonos app?
🤖 Assistant: 🔧 [TOOL] list_native_sonos_playlists()
🔧 [TOOL] create_native_sonos_playlist_from_local(local_playlist='favorites')
🔧 [TOOL] list_native_sonos_playlists()

Perfect! I've successfully created a native Sonos playlist called **favorites** from your local playlist.

Here's what happened:
- I first checked if a playlist with that name already existed on your Sonos system (it didn't)
- I converted your local favorites playlist (8 tracks) into a native Sonos playlist
- The playlist is now available on your Sonos system

You can now access this playlist from:
- Your Sonos mobile app
- Any Sonos controller in your home
- Voice assistants like Alexa

The native playlist and your local playlist are independent - if you update one, the other won't automatically change. Would you like me to play it now?

----------------------------

**Note:** You can use instructions in the system prompt to guide how wordy and sycophantic, enthusiastic etc. the agent will be.  For the moment, I am enjoying its commentary and energy but the instructions can be changed to suit the style of agent you'd prefer. The system prompt contains s summary of the tools that the agent has access to as well as some example scenarios that the agent is intended to manage. 

