from dotenv import load_dotenv
from flask import Flask, request, Response
import os
import subprocess

# Pull configuration details from .env file.
load_dotenv()
TA_HELPER_SCRIPT = os.environ.get("TA_HELPER_SCRIPT")
APPRISE_TRIGGER_PORT = os.environ.get("APPRISE_TRIGGER_PORT")

app = Flask(__name__)
@app.route('/ta-helper-trigger', methods=['POST'])

def return_response():
    print(request.json);
    result = Response(status=200)

    # Kickstart ta-helper script as there have been changes.
    print("TA has made changes to the video archive, invoking helper script.")
    
    # Use Popen so we immediately return and sending apprise doesn't time out.
    subprocess.Popen(["python", TA_HELPER_SCRIPT])
    
    ## Do something with the request.json data.
    return result

if __name__ == "__main__": app.run(host="0.0.0.0", port=APPRISE_TRIGGER_PORT)
