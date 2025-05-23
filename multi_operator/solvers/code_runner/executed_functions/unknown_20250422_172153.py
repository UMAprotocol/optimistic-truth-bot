import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging
import re

# Load environment variables
load_dotenv()

# Constants
DEADLINE_DATE = datetime(2025, 12, 31, 23, 59)  # Deadline for the event
EXPECTED_TERM = "Trump Effect"  # Term to be checked in the speech

# API Keys
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Sensitive data patterns to mask in logs
SENSITIVE_PATTERNS = [
    re.compile(r"YOUTUBE_API_KEY\s*=\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
]

class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        original_msg = record.getMessage()
        masked_msg = original_msg
        for pattern in SENSITIVE_PATTERNS:
            masked_msg = pattern.sub("******", masked_msg)
        record.msg = masked_msg
        return True

# Add sensitive data filter to logger
logger.addFilter(SensitiveDataFilter())

def fetch_youtube_video_content(video_id):
    """
    Fetches the transcript of a YouTube video using the video ID.
    """
    url = f"https://www.googleapis.com/youtube/v3/captions?part=snippet&videoId={video_id}&key={YOUTUBE_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        captions = response.json()
        for item in captions['items']:
            if item['snippet']['language'] == 'en':
                return download_caption(item['id'])
    except requests.RequestException as e:
        logger.error(f"Failed to fetch YouTube video content: {e}")
    return None

def download_caption(caption_id):
    """
    Downloads the actual caption text using the caption ID.
    """
    url = f"https://www.googleapis.com/youtube/v3/captions/{caption_id}?key={YOUTUBE_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Failed to download caption: {e}")
    return None

def check_term_in_transcript(transcript, term):
    """
    Checks if the term exists in the transcript.
    """
    return term.lower() in transcript.lower()

def main():
    # Example video ID - this should be dynamically determined based on the actual video of the press briefing
    video_id = "EXAMPLE_VIDEO_ID"
    transcript = fetch_youtube_video_content(video_id)
    if transcript:
        if check_term_in_transcript(transcript, EXPECTED_TERM):
            print("recommendation: p2")  # Term found
        else:
            print("recommendation: p1")  # Term not found
    else:
        print("recommendation: p3")  # Unable to fetch or process the transcript

if __name__ == "__main__":
    main()