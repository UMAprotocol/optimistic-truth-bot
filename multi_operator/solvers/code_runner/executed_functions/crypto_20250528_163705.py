import requests
import re
import logging
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def get_video_transcript(video_url):
    """
    Placeholder function to simulate fetching a transcript from a video URL.
    This function should be replaced with actual API calls to a service that can extract transcripts.
    """
    # Simulated transcript
    return "Today we discuss the economy and we mention million, billion, trillion each five times."

def count_terms_in_transcript(transcript, terms):
    """
    Count the occurrences of each term in the transcript.
    """
    counts = {term: 0 for term in terms}
    words = re.findall(r'\w+', transcript.lower())  # Extract words and convert to lower case
    for word in words:
        for term in terms:
            if term in word:
                counts[term] += 1
    return counts

def main():
    """
    Main function to process the event and determine the outcome based on the transcript.
    """
    # Terms to be counted in the transcript
    terms = ["million", "billion", "trillion"]
    
    # Simulated video URL from the event
    video_url = "https://example.com/jd-vance-bitcoin-2025"
    
    try:
        # Get the transcript of the video
        transcript = get_video_transcript(video_url)
        logger.info("Transcript retrieved successfully.")
        
        # Count the occurrences of each term
        counts = count_terms_in_transcript(transcript, terms)
        logger.info(f"Counts: {counts}")
        
        # Check if any term is mentioned 5 or more times
        if any(count >= 5 for count in counts.values()):
            print("recommendation: p2")  # Yes
        else:
            print("recommendation: p1")  # No
            
    except Exception as e:
        logger.error(f"Error processing the event: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()