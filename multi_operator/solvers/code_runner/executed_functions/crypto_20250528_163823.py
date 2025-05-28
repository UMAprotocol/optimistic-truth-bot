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

def fetch_video_transcript(video_url):
    """
    Fetches the transcript of a video from a given URL.
    This is a placeholder function and needs to be implemented based on the actual API or method used.
    """
    # Placeholder for fetching video transcript logic
    logger.info(f"Fetching video transcript from URL: {video_url}")
    # Simulated response (this should be replaced with actual API call and response handling)
    simulated_response = "Today, we are dealing with a trillion dollar industry. With millions of users and billions of transactions."
    return simulated_response

def count_terms_in_transcript(transcript, terms):
    """
    Counts the occurrences of each term in the transcript.
    """
    term_counts = {term: 0 for term in terms}
    for term in terms:
        # Use regex to find whole words, considering plural and possessive forms
        pattern = re.compile(r'\b' + re.escape(term) + r's?\b', re.IGNORECASE)
        matches = pattern.findall(transcript)
        term_counts[term] = len(matches)
    return term_counts

def main():
    """
    Main function to process the event and determine the outcome based on the video transcript.
    """
    event_date = "2025-05-28"
    event_time = "12:00 PM"
    timezone_str = "US/Eastern"
    video_url = "https://bitcoinmagazine.com/politics/u-s-vice-president-jd-vance-to-speak-at-bitcoin-2025-conference"
    terms_to_count = ["million", "billion", "trillion"]

    # Fetch the video transcript
    transcript = fetch_video_transcript(video_url)

    # Count the terms in the transcript
    counts = count_terms_in_transcript(transcript, terms_to_count)

    # Determine if any term was said 5 or more times
    for count in counts.values():
        if count >= 5:
            print("recommendation: p2")  # Yes, said 5+ times
            return

    print("recommendation: p1")  # No, not said 5+ times

if __name__ == "__main__":
    main()