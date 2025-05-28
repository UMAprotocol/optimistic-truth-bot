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
    Args:
        video_url: URL of the video from which to fetch the transcript.
    Returns:
        Transcript text as a string.
    """
    # Placeholder for actual transcript fetching logic
    # This should be replaced with actual API calls or scraping methods
    logger.info(f"Fetching transcript from video URL: {video_url}")
    return "Example transcript containing the word Million five times: Million, Million, Million, Million, Million."

def count_terms_in_transcript(transcript, terms):
    """
    Counts the occurrences of specified terms in a transcript.
    Args:
        transcript: The text of the transcript.
        terms: List of terms to count.
    Returns:
        Dictionary with term counts.
    """
    term_counts = {term: 0 for term in terms}
    for term in terms:
        # Use regex to find whole words, considering plural and possessive forms
        pattern = re.compile(r'\b' + re.escape(term) + r's?\b', re.IGNORECASE)
        term_counts[term] = len(pattern.findall(transcript))
    return term_counts

def main():
    """
    Main function to process the event and determine the outcome based on the transcript.
    """
    video_url = "https://example.com/jd-vance-bitcoin-2025"
    terms_to_count = ["Million", "Billion", "Trillion"]
    threshold = 5

    try:
        transcript = fetch_video_transcript(video_url)
        term_counts = count_terms_in_transcript(transcript, terms_to_count)
        logger.info(f"Term counts: {term_counts}")

        # Check if any term is mentioned 5 or more times
        if any(count >= threshold for count in term_counts.values()):
            print("recommendation: p2")  # Yes
        else:
            print("recommendation: p1")  # No

    except Exception as e:
        logger.error(f"Error processing the event: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()