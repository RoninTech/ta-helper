# ta-helper
Python script to post process Tube Archivist products and support NFO files and new video notifications using apprise library.

Copy .example-env to .env in the same folder as the script and edit to put in your own settings.

Script created by user GordonFreeman on the [Tube Archivist discord server](https://www.tubearchivist.com/discord).

It iterates through the Tube Archivist video folders and does several things:

1. Creates a mirror set of folders via symbolic links with the actual channel names and video titles for human readability.
2. When a new video is detected and apprise is enabled, a notification is sent with the new video details and a link to play the video in Tube Archivist.
3. The script also generates .NFO files for each new channel and/or video which allows media managers such as Kodi etc. to show meta info.
4. Symbolic links to subtitle, poster, cover and banner jpg's inside TA cache are also setup for media managers. 

When apprise is setup to send emails via gmail, each notification takes approx 3s on a Raspberry Pi4.  So if you are doing an initial run on a large library, setting USE_APPRISE to "False" will save a lot of time.

Most up to date version of script can be found on GitHub, [here](https://github.com/RoninTech/ta-helper).