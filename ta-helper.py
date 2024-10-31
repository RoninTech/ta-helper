import apprise
from distutils.util import strtobool
from dotenv import load_dotenv
import logging
import os
import requests
import re
import shutil  # For copying files

# Logging setup
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter(fmt='%(asctime)s %(filename)s:%(lineno)s %(levelname)-8s %(message)s',
                              datefmt='%d-%b-%y %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Load configuration from .env file
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

logger.setLevel(os.environ.get("LOGLEVEL", "INFO"))

def setup_new_channel_resources(chan_name, chan_data):
    logger.info("New channel %s, setting up resources.", chan_name)
    if TA_CACHE == "":
        logger.info("TA_CACHE is not available, cannot set up cached files.")
    else:
        # Copy images for file browsers and media managers
        channel_thumb_path = TA_CACHE + chan_data['channel_thumb_url']
        logger.info("Copying cache %s as poster, cover, and folder.jpg.", channel_thumb_path)
        shutil.copy(channel_thumb_path, TARGET_FOLDER + "/" + chan_name + "/" + "poster.jpg")
        shutil.copy(channel_thumb_path, TARGET_FOLDER + "/" + chan_name + "/" + "cover.jpg")
        shutil.copy(channel_thumb_path, TARGET_FOLDER + "/" + chan_name + "/" + "folder.jpg")
        channel_banner_path = TA_CACHE + chan_data['channel_banner_url']
        shutil.copy(channel_banner_path, TARGET_FOLDER + "/" + chan_name + "/" + "banner.jpg")
    
    # Generate tvshow.nfo for media managers, TA_CACHE is not required
    logger.info("Generating %s", TARGET_FOLDER + "/" + chan_name + "/" + "tvshow.nfo")
    with open(TARGET_FOLDER + "/" + chan_name + "/" + "tvshow.nfo","w+") as f:
        f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<tvshow>\n\t<title>' + chan_data['channel_name'] + "</title>\n\t" +
                "<showtitle>" + chan_data['channel_name'] + "</showtitle>\n\t" +
                "<uniqueid>" + chan_data['channel_id'] + "</uniqueid>\n\t" +
                "<plot>" + chan_data['channel_description'] + "</plot>\n\t" +
                "<premiered>" + chan_data['channel_last_refresh'] + "</premiered>\n</episodedetails>")

def generate_new_video_nfo(chan_name, title, video_meta_data):
    logger.info("Generating NFO file and subtitles for %s video: %s", video_meta_data['channel']['channel_name'], video_meta_data['title'])
    video_basename = os.path.splitext(video_meta_data['media_url'])[0]
    shutil.copy(TA_MEDIA_FOLDER + video_basename + ".en.vtt", TARGET_FOLDER + "/" + chan_name + "/" + title.replace(".mp4",".en.vtt"))
    title = title.replace('.mp4','.nfo')
    with open(TARGET_FOLDER + "/" + chan_name + "/" + title,"w+") as f:
        f.write('<?xml version="1.0" ?>\n<episodedetails>\n\t' +
                "<title>" + video_meta_data['title'] + "</title>\n\t" +
                "<showtitle>" + video_meta_data['channel']['channel_name'] + "</showtitle>\n\t" +
                "<uniqueid>" + video_meta_data['youtube_id'] + "</uniqueid>\n\t" +
                "<plot>" + video_meta_data['description'] + "</plot>\n\t" +
                "<premiered>" + video_meta_data['published'] + "</premiered>\n</episodedetails>")

def notify(video_meta_data):
    logger.info("Sending notification about new video %s: %s", video_meta_data['channel']['channel_name'], video_meta_data['title'])
    # Sending notification (simplified for the example)
    video_title = "[TA] New video from " + video_meta_data['channel']['channel_name']
    apobj = apprise.Apprise()
    apobj.add(APPRISE_LINK)
    apobj.notify(body=video_meta_data['description'], title=video_title)

def cleanup_after_deleted_videos():
    logger.info("Checking for broken links and NFO files without videos.")
    for root, dirs, files in os.walk(TARGET_FOLDER):
        for filename in files:
            path = os.path.join(root, filename)
            if not filename == "tvshow.nfo" and filename.endswith(".nfo"):
                expected_video = path.replace('.nfo', '.mp4')
                if not os.path.exists(expected_video):
                    logger.info("Deleting unnecessary file: %s", path)
                    os.remove(path)

def urlify(s):
    s = re.sub(r"[^\w\s]", '', s)
    s = re.sub(r"\s+", '-', s)
    return s

os.makedirs(TARGET_FOLDER, exist_ok=True)
url = TA_SERVER + '/api/channel/'
headers = {'Authorization': 'Token ' + TA_TOKEN}
req = requests.get(url, headers=headers)
if req and req.status_code == 200:
    channels_json = req.json()
    channels_data = channels_json['data']
else:
    logger.info("No channels in TA, exiting.")
    sys.exit()

for channel in channels_data:
    chan_name = urlify(channel['channel_name'])
    try:
        os.makedirs(TARGET_FOLDER + "/" + chan_name, exist_ok=False)
        setup_new_channel_resources(chan_name, channel)
    except OSError:
        logger.debug("Channel folder %s already exists.", chan_name)

    # Pagination for getting all videos
    page = 1
    while True:
        chan_videos = requests.get(url + channel['channel_id'] + f"/video/?page={page}", headers=headers)
        if not chan_videos or chan_videos.status_code != 200:
            break

        chan_videos_data = chan_videos.json().get('data', [])
        if not chan_videos_data:
            break

        for video in chan_videos_data:
            video['media_url'] = video['media_url'].replace('/media', '')
            title = f"{urlify(video['title'])}.mp4"  # Remove date and ID
            try:
                shutil.copy(TA_MEDIA_FOLDER + video['media_url'], TARGET_FOLDER + "/" + chan_name + "/" + title)
                logger.info("New video file %s from %s", title, chan_name)
                if NOTIFICATIONS_ENABLED:
                    notify(video)
                if GENERATE_NFO:
                    generate_new_video_nfo(chan_name, title, video)
            except FileExistsError:
                logger.debug("File %s already exists", title)

        page += 1

# Check for deleted videos and clean up files
if CLEANUP_DELETED_VIDEOS:
    cleanup_after_deleted_videos()
