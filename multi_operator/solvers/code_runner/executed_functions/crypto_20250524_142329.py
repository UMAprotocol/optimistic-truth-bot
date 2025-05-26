import requests
import os
from dotenv import load_dotenv
import logging
import re

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_CBB_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def fetch_video_transcript(url):
    """
    Fetch the transcript of a video from a given URL.
    This is a placeholder function and needs to be implemented based on actual API or method used.
    """
    # Placeholder response, should be replaced with actual API call to fetch video transcript
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return None

def check_for_term_in_transcript(transcript, term):
    """
    Check if the term exists in the transcript.
    """
    return term.lower() in transcript.lower()

def main():
    # URL of the video of Trump's speech at West Point Commencement
    video_url = "https://example.com/trump-west-point-speech"

    # Term to search for in the transcript
    search_term = "lethal"

    try:
        transcript = fetch_video_transcript(video_url)
        if transcript:
            found = check_for_term_in_transcript(transcript, search_term)
            if found:
                print("recommendation: p2")  # Term found, resolve to Yes
            else:
                print("recommendation: p1")  # Term not found, resolve to No
        else:
            print("recommendation: p1")  # No transcript available, resolve to No
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print("recommendation: p1")  # Resolve to No in case of any error

if __name__ == "__main__":
    main()