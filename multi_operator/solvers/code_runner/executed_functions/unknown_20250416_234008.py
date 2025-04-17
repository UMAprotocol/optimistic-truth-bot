import os
import requests
from dotenv import load_dotenv
import logging
from datetime import datetime

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Check if API key is available
if not API_KEY:
    raise ValueError(
        "SPORTS_DATA_IO_MLB_API_KEY not found in environment variables. "
        "Please add it to your .env file."
    )

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def fetch_event_video_content(date):
    """
    Fetches video content for the specified date and event.

    Args:
        date: Event date in YYYY-MM-DD format

    Returns:
        Video content data or None if not found
    """
    logger.info(f"Fetching video content for event on {date}")
    
    # Placeholder URL for video content API
    url = f"https://api.videocontent.io/v1/events/{date}?key={API_KEY}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        video_content = response.json()
        logger.info(f"Retrieved video content for {date}")
        return video_content
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch video content: {e}")
        return None

def analyze_video_content(video_content):
    """
    Analyzes the video content to count occurrences of the word "God".

    Args:
        video_content: Video content data

    Returns:
        Count of the word "God"
    """
    if not video_content:
        logger.info("No video content available")
        return 0

    # Simulate analysis of video content
    word_count = video_content.get("transcript", "").lower().count("god")
    logger.info(f"Word 'God' found {word_count} times in the video")
    return word_count

def main():
    """
    Main function to fetch and analyze video content for the event.
    """
    event_date = "2025-04-16"
    video_content = fetch_event_video_content(event_date)
    
    if video_content is None:
        print("recommendation: p1")  # No video content, resolve to "No"
        return
    
    word_count = analyze_video_content(video_content)
    
    if word_count >= 3:
        print("recommendation: p2")  # Word "God" said 3+ times, resolve to "Yes"
    else:
        print("recommendation: p1")  # Word "God" said less than 3 times, resolve to "No"

if __name__ == "__main__":
    main()