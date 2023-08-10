import base64
from distutils.util import strtobool
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.oauth2 import service_account
from googleapiclient.discovery import build
import html2text
import json
import logging
import requests
import re
import os

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter(fmt='%(asctime)s %(filename)s:%(lineno)s %(levelname)-8s %(message)s',
                              datefmt='%d-%b-%y %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Pull configuration details from .env file.
load_dotenv()
ENABLE_EMAIL_NOTIFICATIONS = bool(strtobool(os.environ.get("ENABLE_EMAIL_NOTIFICATIONS", 'False')))
GENERATE_NFO = bool(strtobool(os.environ.get("GENERATE_NFO", 'False')))
GSAPI_NAME = os.environ.get("GOOGLE_SERVICE_NAME")
GSAPI_VERSION = os.environ.get("GOOGLE_SERVICE_VERSION")
GSAPI_SCOPE = json.loads(os.environ.get("GOOGLE_SERVICE_SCOPE"))
GSAPI_ACCOUNT_FILE = os.environ.get("GOOGLE_SERVICE_ACCOUNT_SECRETS")
FROMADDR = os.environ.get("MAIL_USER")
RECIPIENTS = os.environ.get("MAIL_RECIPIENTS")
RECIPIENTS = RECIPIENTS.split(',')
TA_MEDIA_FOLDER = os.environ.get("TA_MEDIA_FOLDER")
TA_SERVER = os.environ.get("TA_SERVER")
TA_TOKEN = os.environ.get("TA_TOKEN")
TARGET_FOLDER = os.environ.get("TARGET_FOLDER")

logger.setLevel(os.environ.get("LOGLEVEL", "INFO"))

def generate_nfo(chan_name, title, video_meta_data):
    logger.debug("Generating NFO file for %s video: %s", video_meta_data['channel']['channel_name'], video_meta_data['title'])

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
    # Switched to Googles new Gmail API with Service Account for
    # secure sending emails with Gmail account.
    logger.debug("Using Service Account tokens file: %s",
                GSAPI_ACCOUNT_FILE)

    credentials = service_account.Credentials.from_service_account_file(
        filename=GSAPI_ACCOUNT_FILE,
        scopes=GSAPI_SCOPE,
        subject=FROMADDR)

    service_gmail = build(GSAPI_NAME, GSAPI_VERSION, credentials=credentials)
    response = service_gmail.users().getProfile(userId='me').execute()
    logger.debug(response)

    email_body = '<!DOCTYPE PUBLIC “-//W3C//DTD XHTML 1.0 Transitional//EN” '
    email_body += '“https://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd”>' + '\n'
    email_body += '<html xmlns="http://www.w3.org/1999/xhtml">' + '\n'
    email_body += '<head>' + '\n\t'
    email_body += '<title>' + video_meta_data['title'] + '</title>' + '\n'
    email_body += '</head>' + '\n'
    email_body += '<body>'

    video_url = TA_SERVER + "/video/" + video_meta_data['youtube_id'] + "<br>" + '\n'
    email_body += "\n\n<b>Video Title:</b> " + video_meta_data['title']  + "<br>" + '\n'
    email_body += "\n<b>Video Date:</b> " + video_meta_data['published'] + "<br>" + '\n'
    email_body += "\n<b>Video Views:</b> " + str(video_meta_data['stats']['view_count']) + "<br>" + '\n'
    email_body += "\n<b>Video Likes:</b> " + str(video_meta_data['stats']['like_count']) + "<br>" + '\n\n'
    email_body += "\n<b>Video Link:</b> " + video_url + "<br>" + '\n'
    email_body += "\n<b>Video Description:</b>\n\n<pre>" + video_meta_data['description'] + '</pre></br>\n\n'
    email_body += '\n</body>\n</html>'
    # Dump for local viewing
    pretty_text = html2text.HTML2Text()
    pretty_text.ignore_links = True
    pretty_text.body_width = 200
    logger.debug(pretty_text.handle(email_body))
    logger.debug(email_body)

    mime_message = MIMEMultipart()
    mime_message['to'] = ", ".join(RECIPIENTS)
    mime_message['subject'] = (f"TA Notify: New video from "
                            f"{video_meta_data['channel']['channel_name']} YouTube Channel")
    mime_message.attach(MIMEText(email_body, 'html'))
    raw_string = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

    try:
        logger.info(
            "Emailing interested parties via Gmail:Service Account")
        message = service_gmail.users().messages().send(
            userId='me', body={'raw': raw_string}).execute()
        logger.debug('Message Id: %s', message['id'])
    except errors.HttpError as error:
        logger.error("An error occurred sending email: %s", error)

def urlify(s):
    s = re.sub(r"[^\w\s]", '', s)
    s = re.sub(r"\s+", '-', s)
    return s

os.makedirs(TARGET_FOLDER, exist_ok = True)
url = TA_SERVER + '/api/channel/'
headers = {'Authorization': 'Token ' + TA_TOKEN}
req = requests.get(url, headers=headers)
channels_json = req.json() if req and req.status_code == 200 else None
chan_data = channels_json['data']

while channels_json['paginate']['last_page']:
    channels_json = requests.get(url, headers=headers, params={'page': channels_json['paginate']['current_page'] + 1}).json()
    chan_data.extend(channels_json['data'])
                     
for x in chan_data:
    chan_name = urlify(x['channel_name'])
    description = x['channel_description']
    logger.debug("Video Description: " + description)
    logger.debug("Channel Name: " + chan_name)
    if(len(chan_name) < 1): chan_name = x['channel_id']
    chan_url = url+x['channel_id']+"/video/"
    os.makedirs(TARGET_FOLDER + "/" + chan_name, exist_ok = True)
    logger.debug("Channel URL: " + chan_url)
    chan_videos = requests.get(chan_url, headers=headers)
    chan_videos_json = chan_videos.json() if chan_videos and chan_videos.status_code == 200 else None

    if chan_videos_json is not None:
        chan_videos_data = chan_videos_json['data']
        while chan_videos_json['paginate']['last_page']:
            chan_videos_json = requests.get(chan_url, headers=headers, params={'page': chan_videos_json['paginate']['current_page'] + 1}).json()
            chan_videos_data.extend(chan_videos_json['data'])

        for y in chan_videos_data:
            y['media_url'] = y['media_url'].replace('/media','')
            logger.debug(y['published'] + "_" + y['youtube_id'] + "_" + urlify(y['title']) + ", " + y['media_url'])
            title=y['published'] + "_" + y['youtube_id'] + "_" + urlify(y['title']) + ".mp4"
            try:
                os.symlink(TA_MEDIA_FOLDER + y['media_url'], TARGET_FOLDER + "/" + chan_name + "/" + title)
                # Getting here means a new video.
                logger.info("Processing new video from %s: %s\n", chan_name, title)
                if ENABLE_EMAIL_NOTIFICATIONS:
                    notify(y)
                if GENERATE_NFO:
                    generate_nfo(chan_name, title, y)
            except FileExistsError:
                # This means we already had processed the video, completely normal.
                logger.debug("Symlink exists for " + title)
                
