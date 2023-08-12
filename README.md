# ta-helper
Python script to post process Tube Archivist products and support NFO files and new video notifications using apprise library.

Copy .example-env to .env in the same folder as the script and edit to put in your own settings.

Script created by user GordonFreeman on the [Tube Archivist discord server](https://www.tubearchivist.com/discord).

It iterates through the Tube Archivist video folders and does several things:

1. Creates a mirror set of folders via symbolic links with the actual channel names and video titles for human readability.
2. Generates .NFO files for each new channel and/or video which allows media managers such as Kodi, Emby, Jellyfin etc. to show meta info.
3. Symbolic links to subtitles, poster, cover and banner jpg's inside TA cache are setup for media managers.
4. Finally, if NOTIFICATIONS_ENABLED is set to "True" in your .env, apprise will be used to notify of new videos using the apprise URL you provide, also in .env, based off the [apprise documentation](https://github.com/caronc/apprise/wiki). Here i san example of an apprise link to send notification via Gmail: "mailto://<username>:<password>@gmail.com"

**NOTE:** When apprise is setup to send emails via gmail, each notification takes approx 3s on a Raspberry Pi4.  So if you are doing an initial run on a large library, temporarily setting NOTIFICATIONS_ENABLED to "False" will save a lot of time.

## Triggering ta-helper to run:

To kickstart the ta-helper when TA adds new videos to the archive we have 2 options:

1. Use a cron job to periodically run the script, say every half an hour.  Using crontab -e to add a cron job.  This would trigger it every 30 minutes: 30 * * * * python /home/me/projects/ta-helper/ta-helper.py

2. Use apprise notifications from TA server as event driven triggers to run the script only when needed.  We use apprise via the Settings page.  Under "Start Download" set the apprise notification URL to "json://<IP/Hostname>:<PORT>/ta-helper-trigger".  For example I use: "json://192.168.1.11:8001/ta-helper-trigger".  **NOTE**: Remove the quotes before copying into TA settings.  To process these notifications and trigger the script, simply run "python ta-helper-trigger.py" on the machine where your TA archive is.  Make sure the PORT value in ta-helper-trigger.py matches the PORT you used in the TA apprise link mentioned above.  I added the following line (without quotes) as a cron job (using crontab -e): "@reboot python /home/me/projects/ta-helper/ta-helper-trigger.py"

Most up to date version of script can be found on GitHub, [here](https://github.com/RoninTech/ta-helper).