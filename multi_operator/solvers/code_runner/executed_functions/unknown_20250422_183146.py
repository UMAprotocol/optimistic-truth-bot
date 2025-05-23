import os
import requests
import re
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging
import json

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants - RESOLUTION MAPPING using internal abbreviations
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "Unknown": "p3",
    "Too early to resolve": "p4",
}

# Sensitive data patterns to mask in logs
SENSITIVE_PATTERNS = [
    re.compile(r"SPORTS_DATA_IO_NBA_API_KEY\s*=\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
    re.compile(r"api_key\s*=\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
    re.compile(r"key\s*=\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
    re.compile(r"Authorization\s*:\s*['\"]?[\w-]+['\"]?", re.IGNORECASE),
]

class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        original_msg = record.getMessage()
        masked_msg = original_msg
        for pattern in SENSITIVE_PATTERNS:
            masked_msg = pattern.sub("******", masked_msg)
        record.msg = masked_msg
        return True

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

console_handler.addFilter(SensitiveDataFilter())

logger.addHandler(console_handler)

def fetch_video_transcript(video_url):
    """
    Fetches the transcript of a video from a given URL.
    
    Args:
        video_url: URL of the video whose transcript is to be fetched.
    
    Returns:
        Transcript text or None if an error occurs.
    """
    logger.info(f"Fetching video transcript from {video_url}")
    try:
        response = requests.get(video_url)
        response.raise_for_status()
        transcript_data = response.json()
        return transcript_data.get('transcript', None)
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch video transcript: {e}")
        return None

def check_term_in_transcript(transcript, term):
    """
    Checks if a term is mentioned in the transcript.
    
    Args:
        transcript: Text of the transcript.
        term: Term to search for.
    
    Returns:
        True if term is found, False otherwise.
    """
    logger.info(f"Searching for term '{term}' in transcript")
    return term.lower() in transcript.lower()

def main():
    """
    Main function to determine if Karoline Leavitt said "Sex" in the next White House press briefing.
    """
    # Define the term and video URL
    term = "Sex"
    video_url = "https://api.example.com/whitehouse/pressbriefing/latest"
    
    # Fetch the video transcript
    transcript = fetch_video_transcript(video_url)
    
    if transcript is None:
        logger.error("No transcript available, resolving as 'Too early to resolve'")
        print(f"recommendation: {RESOLUTION_MAP['Too early to resolve']}")
        return
    
    # Check if the term is mentioned in the transcript
    term_found = check_term_in_transcript(transcript, term)
    
    # Determine resolution based on whether the term was found
    resolution = RESOLUTION_MAP["Yes"] if term_found else RESOLUTION_MAP["No"]
    
    # Output the recommendation
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()