import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging
import re

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "Unknown": "p3"
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_white_house_briefing_video():
    """
    Simulates fetching a video of a White House press briefing.
    In a real scenario, this function would interface with an API or a database.
    """
    # This is a placeholder function. In practice, you would replace this with actual API calls.
    return "Video content where Karoline Leavitt says 'Kick us off'."

def check_phrase_in_video(video_content, phrase):
    """
    Checks if the specified phrase is present in the video content.
    """
    return phrase in video_content

def main():
    # Define the phrase to search for
    phrase = "Kick us off"
    
    # Fetch the latest White House press briefing video
    video_content = fetch_white_house_briefing_video()
    
    # Check if the phrase is in the video
    if check_phrase_in_video(video_content, phrase):
        recommendation = RESOLUTION_MAP["Yes"]
    else:
        recommendation = RESOLUTION_MAP["No"]
    
    # Print the recommendation
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()