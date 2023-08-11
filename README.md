# ta-helper
Python script to post process Tube Archivist products and support NFO files and new video email notifications

Copy .example-env to .env in the same folder as the script and edit to put in your own settings.

Script created by user GordonFreeman on the [Tube Archivist discord server](https://www.tubearchivist.com/discord).

It iterates through the Tube Archivist video folders and does several things:

1. Creates a mirror set of folders via symbolic links with the actual channel names and video titles for human readability.
2. When a new video is detected it sends a notification email with the new video details and a link to play the video in Tube Archivist.
3. The script also generates .NFO files for each video which allows media managers such as Kodi etc. to show video meta info.
