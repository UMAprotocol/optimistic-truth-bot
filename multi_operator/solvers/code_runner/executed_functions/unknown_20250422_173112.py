import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging
import re

# Load environment variables
load_dotenv()

# Constants
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Sensitive data patterns to mask in logs
SENSITIVE_PATTERNS = [
    re.compile(r"SPORTS_DATA_IO_NBA_API_KEY\s*=\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
    re.compile(r"api_key\s*=\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
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

def fetch_video_transcript():
    """
    Fetches the transcript of the latest White House press briefing video.
    """
    # Placeholder for actual API call to fetch video transcript
    # This function should be implemented to interact with a video processing API
    # that can extract spoken words from a video.
    return "Today, we kick us off with a briefing on the current economic policies."

def check_phrase_in_transcript(phrase):
    """
    Checks if the specified phrase is in the transcript of the latest White House press briefing.
    """
    transcript = fetch_video_transcript()
    # Normalize the transcript and phrase for reliable searching
    normalized_transcript = transcript.lower()
    normalized_phrase = phrase.lower()
    return normalized_phrase in normalized_transcript

def main():
    """
    Main function to determine if Karoline Leavitt said "Kick us off" in the latest White House press briefing.
    """
    phrase = "Kick us off"
    if check_phrase_in_transcript(phrase):
        print("recommendation: p2")  # Corresponds to "Yes"
    else:
        print("recommendation: p1")  # Corresponds to "No"

if __name__ == "__main__":
    main()