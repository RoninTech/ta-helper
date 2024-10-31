# ta-helper

Python script to post-process Tube Archivist products, generate human-readable folders and files, support NFO files, and send notifications for new videos using the apprise library. Various functions can be enabled or disabled. Nothing is touched in your Tube Archivist media folders. The image below shows your original obfuscated naming on the left and new, human-readable folders on the right.

![Screenshot from 2023-08-12 16-56-04](https://github.com/RoninTech/ta-helper/assets/226861/4cf31133-8d40-4a93-b363-cf8f26054f25)

Here is how your NFO file supporting media managers (Kodi, Emby, Jellyfin, etc.) can look after you add your new YouTube videos folder:

![screenshot00000](https://github.com/RoninTech/ta-helper/assets/226861/b2625c9f-c600-43ac-9b72-cdacc9f6ea7f)

![screenshot00002](https://github.com/RoninTech/ta-helper/assets/226861/ad2a539a-3b84-4045-9c98-4e78886ae3db)

## Using It

Copy `.example-env` to `.env` in the same folder as the script and edit it to put in your own settings. `.example-env` has detailed comments that explain how to use each setting.

## What exactly does it do?

It iterates through the Tube Archivist video folders and performs several actions:

1. Creates a mirror set of folders with the actual channel names and video titles for human readability.
2. If `GENERATE_NFO` is set to "True," it will generate `.nfo` files for each new channel and/or video, allowing media managers such as Kodi, Emby, Jellyfin, etc., to display meta info.
3. If `TA_CACHE` is not empty, it can generate symbolic links to subtitles, posters, covers, and banner JPGs inside TA cache for media managers.
4. If `NOTIFICATIONS_ENABLED` is set to "True" in your `.env`, apprise will be used to notify of new videos using the apprise URL you provide, also in `.env`, based on the [apprise documentation](https://github.com/caronc/apprise/wiki). Here is an example of an apprise link to send notifications via Gmail: `"mailto://<username>:<password>@gmail.com"`
5. If `CLEANUP_DELETED_VIDEOS` is set to "True," any broken symlinks or dangling NFO files (NFO files with no corresponding video) will be deleted from `TARGET_FOLDER`. If Tube Archivist is configured to delete watched videos, this will clean up any leftovers.

### Changes in this Fork

This fork, created by user Lap_Jap, introduces the following changes:

- Copies and renames video files instead of creating symbolic links, allowing sharing of videos without YouTube access.
- Excludes the date and ID from video file names for a cleaner format.

**NOTE:** When apprise is set up to send emails via Gmail, each notification takes approximately 3 seconds on a Raspberry Pi 4. So if you are doing an initial run on a large library, temporarily setting `NOTIFICATIONS_ENABLED` to "False" will save a lot of time.

## Triggering ta-helper to run:

To kickstart the ta-helper when Tube Archivist adds new videos to the archive, we have three options:

1. Manually run the script when you know new videos have been added via `"python ta-helper.py"`
   
2. Use a cron job to periodically run the script, say every half an hour. Use `crontab -e` to add a cron job. This would trigger it every 30 minutes: 

30 * * * * python /home/me/projects/ta-helper/ta-helper.py


3. Use apprise notifications from the Tube Archivist server as event-driven triggers to run the script only when needed. This is more efficient than cron polling described in (2) above. We use apprise via the Settings page. Under "Start Download," set the apprise notification URL to `"json://<IP/Hostname>:<PORT>/ta-helper-trigger"`. For example, I use: `"json://192.168.1.11:8001/ta-helper-trigger"`. **NOTE:** Remove the quotes before copying into Tube Archivist settings. To process these notifications and trigger the script, simply run `"python ta-helper-trigger.py"` on the machine where your Tube Archivist archive is located. Make sure the PORT value in `ta-helper-trigger.py` matches the PORT you used in the Tube Archivist apprise link mentioned above. I added the following line (without quotes) as a cron job (using `crontab -e`):

@reboot python /home/me/projects/ta-helper/ta-helper-trigger.py > /home/me/Desktop/ta-trigger.log

Change these paths to match your own configuration.

The most up-to-date version of the script can be found on GitHub, [here](https://github.com/RoninTech/ta-helper).

Script originally created by user GordonFreeman on the [Tube Archivist Discord server](https://www.tubearchivist.com/discord).  
This fork was made by user Lap_Jap on the same Discord server.
