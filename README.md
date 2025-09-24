# CLI application to interact with Sonos speakers

A command-line interface (CLI) application to interact with Sonos speakers, allowing users to control playback, search for tracks and albums, and manage the Sonos queue and provide play-pause, volume control, etc. I prefer to type my music requests than use a voice interface or the Sonos mobile app.

Based on the SoCo python package.

Also has a separate Sonos music agent employing the Claude SDK that uses the Sonos CLI app to perform Sonos-related actions. The various Sonos commands are exposed as tools (functions) that the agent can call.

So things you should be able to do with the agent include:

What tracks are currently on the queue?

What track is playing?

Play some music by a specific artist

Clear the queue

Skip to the next track

Requests can be relatively complicated such as:
  - a live version of Heart of Gold by Neil Young.
  - a cover of Take it Down by Patty Griffin
  -


