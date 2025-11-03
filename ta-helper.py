import apprise
from distutils.util import strtobool
from dotenv import load_dotenv
from typing import Union
from pathlib import Path
import html2text
import logging
import os
import requests
import re
import sys
import time

# Configure logging.
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter(fmt='%(asctime)s %(filename)s:%(lineno)s %(levelname)-8s %(message)s',
                              datefmt='%d-%b-%y %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Pull configuration details from .env file.
load_dotenv()
NOTIFICATIONS_ENABLED = bool(strtobool(os.environ.get("NOTIFICATIONS_ENABLED", 'False')))
GENERATE_NFO = bool(strtobool(os.environ.get("GENERATE_NFO", 'False')))
FROMADDR = str(os.environ.get("MAIL_USER"))
RECIPIENTS = str(os.environ.get("MAIL_RECIPIENTS"))
RECIPIENTS = RECIPIENTS.split(',')
TA_MEDIA_FOLDER = str(os.environ.get("TA_MEDIA_FOLDER"))
TA_SERVER = str(os.environ.get("TA_SERVER"))
TA_TOKEN = str(os.environ.get("TA_TOKEN"))
TA_CACHE = str(os.environ.get("TA_CACHE"))
TARGET_FOLDER = str(os.environ.get("TARGET_FOLDER"))
APPRISE_LINK = str(os.environ.get("APPRISE_LINK"))
QUICK = bool(strtobool(os.environ.get("QUICK", 'True')))
CLEANUP_DELETED_VIDEOS = bool(strtobool(str(os.environ.get("CLEANUP_DELETED_VIDEOS"))))
CREATE_RELATIVE_SYMLINKS= bool(strtobool(str(os.environ.get("CREATE_RELATIVE_SYMLINKS"))))
logger.setLevel(os.environ.get("LOGLEVEL", "INFO"))

def setup_new_channel_resources(chan_name, chan_data):
    logger.info("New Channel %s, setup resources.", chan_name)
    if TA_CACHE == "":
        logger.info("No TA_CACHE available so cannot setup symlinks to cache files.")
    else:
        # Link the channel logo from TA docker cache into target folder for media managers
        # and file explorers.  Provide cover.jpg, poster.jpg and banner.jpg symlinks.
        channel_thumb_path = TA_CACHE + chan_data['channel_thumb_url']
        logger.info("Symlink cache %s thumb to poster, cover and folder.jpg files.", channel_thumb_path)
        os.symlink(channel_thumb_path, TARGET_FOLDER + "/" + chan_name + "/" + "poster.jpg")
        os.symlink(channel_thumb_path, TARGET_FOLDER + "/" + chan_name + "/" + "cover.jpg")
        os.symlink(channel_thumb_path, TARGET_FOLDER + "/" + chan_name + "/" + "folder.jpg")
        channel_banner_path = TA_CACHE + chan_data['channel_banner_url']
        os.symlink(channel_banner_path, TARGET_FOLDER + "/" + chan_name + "/" + "banner.jpg")
    
    # Generate tvshow.nfo for media managers, no TA_CACHE required.
    logger.info("Generating %s", TARGET_FOLDER + "/" + chan_name + "/" + "tvshow.nfo")
    f= open(TARGET_FOLDER + "/" + chan_name + "/" + "tvshow.nfo","w+")
    f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + '\n'
            '<tvshow>' + '\n\t' + '<title>' +
            chan_data['channel_name'] + "</title>\n\t" +
            "<showtitle>" + chan_data['channel_name'] + "</showtitle>\n\t" +
            "<uniqueid>" + chan_data['channel_id'] + "</uniqueid>\n\t" +
            "<plot>" + chan_data['channel_description'] + "</plot>\n\t" +
            "<premiered>" + chan_data['channel_last_refresh'] + "</premiered>\n</episodedetails>")
    f.close()


def relative_symlink(target: Union[Path, str], destination: Union[Path, str]):
    """Create a symlink pointing to ``target`` from ``location``.
    Args:
        target: The target of the symlink (the file/directory that is pointed to)
        destination: The location of the symlink itself.
    """
    target = Path(target)
    destination = Path(destination)
    target_dir = destination.parent
    target_dir.mkdir(exist_ok=True, parents=True)
    relative_source = os.path.relpath(target, target_dir)
    dir_fd = os.open(str(target_dir.absolute()), os.O_RDONLY)
    logger.info(f"{relative_source} -> {destination.name} in {target_dir}")
    try:
        os.symlink(relative_source, destination.name, dir_fd=dir_fd)
    finally:
        os.close(dir_fd)

def generate_new_video_nfo(chan_name, title, video_meta_data):
    logger.info("Generating NFO file and subtitle symlink for %s video: %s", video_meta_data['channel']['channel_name'], video_meta_data['title'])
    # TA has added a new video.  Create a symlink to subtitles and an NFO file for media managers.
    video_basename = os.path.splitext(video_meta_data['media_url'])[0]
    if (CREATE_RELATIVE_SYMLINKS):
        relative_symlink(TA_MEDIA_FOLDER + video_basename + ".en.vtt", TARGET_FOLDER + "/" + chan_name + "/" + title.replace(".mp4",".en.vtt"))
    else:
        os.symlink(TA_MEDIA_FOLDER + video_basename + ".en.vtt", TARGET_FOLDER + "/" + chan_name + "/" + title.replace(".mp4",".en.vtt"))
    title = title.replace('.mp4','.nfo')
    f= open(TARGET_FOLDER + "/" + chan_name + "/" + title,"w+")
    f.write('<?xml version="1.0" ?>\n<episodedetails>\n\t' +
        "<title>" + video_meta_data['title'] + "</title>\n\t" +
        "<showtitle>" + video_meta_data['channel']['channel_name'] + "</showtitle>\n\t" +
        "<uniqueid>" + video_meta_data['youtube_id'] + "</uniqueid>\n\t" +
        "<plot>" + video_meta_data['description'] + "</plot>\n\t" +
        "<premiered>" + video_meta_data['published'] + "</premiered>\n</episodedetails>")
    f.close()

def notify(video_meta_data):

    # Send a notification via apprise library.
    logger.info("Sending new %s video notification: %s", video_meta_data['channel']['channel_name'],
                video_meta_data['title'])

    email_body = '<!DOCTYPE PUBLIC “-//W3C//DTD XHTML 1.0 Transitional//EN” '
    email_body += '“https://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd”>' + '\n'
    email_body += '<html xmlns="http://www.w3.org/1999/xhtml">' + '\n'
    email_body += '<head>' + '\n\t'
    email_body += '<title>' + video_meta_data['title'] + '</title>' + '\n'
    email_body += '</head>' + '\n'
    email_body += '<body>'

    video_url = TA_SERVER + "/video/" + video_meta_data['youtube_id']
    email_body += "\n\n<b>Video Title:</b> " + video_meta_data['title']  + "<br>" + '\n'
    email_body += "\n<b>Video Date:</b> " + video_meta_data['published'] + "<br>" + '\n'
    email_body += "\n<b>Video Views:</b> " + str(video_meta_data['stats']['view_count']) + "<br>" + '\n'
    email_body += "\n<b>Video Likes:</b> " + str(video_meta_data['stats']['like_count']) + "<br>" + '\n\n'
    email_body += "\n<b>Video Link:</b> <a href=\"" + video_url + "\">" + video_url + "</a><br>" + '\n'
    email_body += "\n<b>Video Description:</b>\n\n<pre>" + video_meta_data['description'] + '</pre></br>\n\n'
    email_body += '\n</body>\n</html>'

    # Dump for local debug viewing
    pretty_text = html2text.HTML2Text()
    pretty_text.ignore_links = True
    pretty_text.body_width = 200
    logger.debug(pretty_text.handle(email_body))
    logger.debug(email_body)

    video_title = "[TA] New video from " + video_meta_data['channel']['channel_name']

    apobj = apprise.Apprise()
    apobj.add(APPRISE_LINK)
    apobj.notify(body=email_body,title=video_title)

def cleanup_after_deleted_videos():
    logger.info("Check for broken symlinks and nfo files without videos in our target folder.")
    broken = []
    for root, dirs, files in os.walk(TARGET_FOLDER):
        if root.startswith('./.git'):
            # Ignore the .git directory.
            continue
        for filename in files:
            path = os.path.join(root,filename)
            file_info = os.path.splitext(path)
            # Check if the file is a video's nfo file
            if not filename == "tvshow.nfo" and file_info[1] == ".nfo" :
                # Check if there is a corresponding video file and if not, delete the nfo file.
                expected_video = path.replace('.nfo','.mp4')
                if not os.path.exists(expected_video):
                    logger.info("Found hanging .nfo file: %s", path)
                    # Queue the hanging nfo file for deletion.
                    broken.append(path)
            elif os.path.islink(path):
                # We've found a symlink.
                target_path = os.readlink(path)
                # Resolve relative symlinks
                if not os.path.isabs(target_path):
                    target_path = os.path.join(os.path.dirname(path),target_path)     
                if not os.path.exists(target_path):
                    # The symlink is broken.
                    broken.append(path)
            else:
                # If it's not a symlink or hanging nfo file, we're not interested.
                logger.debug("No need to clean-up  %s", path)
                continue
        for dir in dirs:
            logger.debug("Found channel folder: %s", dir)

    if broken == []:
        logger.info("No deleted videos found, no cleanup required.")
    else:
        logger.info('%d Broken symlinks found...', len(broken))
        for link in broken:
            logger.info("Deleting file: %s", link )
            # Here we need to delete the NFO file and video and subtitle symlinks
            # associated with the deleted video.
            os.remove(link)
            # TBD Also check TA if channel target folder should be deleted?

def urlify(s):
    s = re.sub(r"[^\w\s]", '', s)
    s = re.sub(r"\s+", '-', s)
    return s

os.makedirs(TARGET_FOLDER, exist_ok = True)
url = TA_SERVER + '/api/channel/'
headers = {'Authorization': 'Token ' + TA_TOKEN}
req = requests.get(url, headers=headers)
if req and req.status_code == 200:
    channels_json = req.json() 
    channels_data = channels_json['data']
else :
    logger.info("No Channels in TA, exiting")
    # Bail from program as we have no channels in TA.
    sys.exit()

while channels_json['paginate']['last_page']:
    channels_json = requests.get(url, headers=headers, params={'page': channels_json['paginate']['current_page'] + 1}).json()
    channels_data.extend(channels_json['data'])
                     
for channel in channels_data:
    chan_name = urlify(channel['channel_name'])
    # some channels have False as channel_description, which later on gives a type error
    if not channel['channel_description']:
        channel['channel_description'] = ""
    description = channel['channel_description']
    logger.debug("Video Description: " + description)
    logger.debug("Channel Name: " + chan_name)
    if(len(chan_name) < 1): chan_name = channel['channel_id']
    chan_url = url+channel['channel_id']+"/video/"
    try:
        os.makedirs(TARGET_FOLDER + "/" + chan_name, exist_ok = False)
        setup_new_channel_resources(chan_name, channel)
    except OSError as error:
        logger.debug("We already have %s channel folder", chan_name)

    logger.debug("Channel URL: " + chan_url)
    chan_videos = requests.get(chan_url, headers=headers)
    chan_videos_json = chan_videos.json() if chan_videos and chan_videos.status_code == 200 else None

    if chan_videos_json is not None:
        chan_videos_data = chan_videos_json['data']
        while chan_videos_json['paginate']['last_page']:
            chan_videos_json = requests.get(chan_url, headers=headers, params={'page': chan_videos_json['paginate']['current_page'] + 1}).json()
            chan_videos_data.extend(chan_videos_json['data'])

        for video in chan_videos_data:
            video['media_url'] = video['media_url'].replace('/media','')
            logger.debug(video['published'] + "_" + video['youtube_id'] + "_" + urlify(video['title']) + ", " + video['media_url'])
            title=video['published'] + "_" + video['youtube_id'] + "_" + urlify(video['title']) + ".mp4"
            try:
                if (CREATE_RELATIVE_SYMLINKS):
                    relative_symlink(TA_MEDIA_FOLDER + video['media_url'], TARGET_FOLDER + "/" + chan_name + "/" + title)
                else:
                    os.symlink(TA_MEDIA_FOLDER + video['media_url'], TARGET_FOLDER + "/" + chan_name + "/" + title)
                # Getting here means a new video.
                logger.info("Processing new video from %s: %s", chan_name, title)
                if NOTIFICATIONS_ENABLED:
                    notify(video)
                else:
                    logger.debug("Notification not sent for %s new video: %s as NOTIFICATIONS_ENABLED is set to False in .env settings.", chan_name, title)
                if GENERATE_NFO:
                    generate_new_video_nfo(chan_name, title, video)
                else:
                    logger.debug("Not generating NFO files for %s new video: %s as GENERATE_NFO is et to False in .env settings.", chan_name, title)
            except FileExistsError:
                # This means we already had processed the video, completely normal.
                logger.debug("Symlink exists for " + title)
                if(QUICK):
                    time.sleep(.5)
                    break;

# If enabled, check for deleted video and if found cleanup video NFO file and video and subtitle symlinks.
if CLEANUP_DELETED_VIDEOS:
    cleanup_after_deleted_videos()
