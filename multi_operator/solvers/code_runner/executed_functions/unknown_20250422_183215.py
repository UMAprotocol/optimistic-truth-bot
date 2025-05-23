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
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_video_transcript(video_url):
    """
    Simulated function to fetch transcript from a video URL.
    This is a placeholder for actual implementation.
    """
    # This is a placeholder. In a real scenario, you would use an API or a service to extract transcripts.
    return "This is a sample transcript where Karoline Leavitt says 'sex' in the context of a discussion."

def check_term_in_transcript(transcript, term):
    """
    Check if the term is mentioned in the transcript.
    """
    # Using regex to find the term in the transcript, considering plural and possessive forms.
    pattern = re.compile(r'\b' + re.escape(term) + r's?\b', re.IGNORECASE)
    if pattern.search(transcript):
        return True
    return False

def main():
    # Define the term to search for in the transcript
    term = "sex"
    
    # Simulated video URL (In a real scenario, this would be dynamically determined)
    video_url = "http://example.com/whitehouse_briefing.mp4"
    
    # Fetch the transcript from the video
    transcript = fetch_video_transcript(video_url)
    
    # Check if the term is mentioned in the transcript
    if check_term_in_transcript(transcript, term):
        recommendation = RESOLUTION_MAP["Yes"]
    else:
        recommendation = RESOLUTION_MAP["No"]
    
    # Print the recommendation
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()