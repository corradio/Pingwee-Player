Pingwee-Player
==============

This a client/server music player based on MPD and websockets. It was built because I was tired of iTunes, and wanted a proper open alternative I could hack around with. This is still very experimental.

The program is based on the idea that the library should be referenced by 'Tags' (like labels in GMail). There should be a simple interface for tagging, and constructing playlists by selecting tags. Some tags can be specially marked, i.e. 'Cloud' for syncing songs to the cloud for offline listening, or 'Burn' for burning them to disc.
Currently MP3s and FLACs are supported.

A Python server handles IO with the music library, maintains database, and communicates with a local MPD client for playback.
The client/server communication is established through websockets.
A webclient example is implemented using AngularJS.

There are x abstractions:
* cdburner.py: Handles CD burning through cdrecord.
* cloudsyncer.py: [EXPERIMENTAL] Syncs some tags to the cloud for offline mobile listening.
* coverart.py: [EXPERIMENTAL] A try to automatically fetch covers from the web.
* library.py: Handles IO with the music files. Writes ID3 tags and handles data structures.
* player.py: Handles playback (by wrapping MPD) and queues.
* server.py: Main point of entry. Exposes the websocket, handles inbound and outbound communication.

Communication syntax
-------------------

To be done
  
Comments
--------

Feedback is always greatly appreciated!
