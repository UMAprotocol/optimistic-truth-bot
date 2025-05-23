import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging
import re

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NFL_API_KEY")

# Constants
DEADLINE_DATE = datetime(2025, 12, 31, 23, 59)  # Deadline for the event
EXPECTED_TERMS = ["sex", "sexes", "sex's"]  # Expected terms including plural and possessive forms

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_white_house_briefing_videos():
    """
    Simulated function to fetch video transcripts of White House briefings.
    This function is a placeholder and should be replaced with actual API calls or methods
    to retrieve and process video transcripts.
    """
    # Placeholder response simulating the content of a briefing
    simulated_response = "Today we discuss several topics including taxes and the economy..."
    return simulated_response

def check_term_in_transcript(transcript, terms):
    """
    Check if any of the specified terms are present in the transcript.
    
    Args:
        transcript (str): The text of the transcript.
        terms (list): List of terms to check in the transcript.
    
    Returns:
        bool: True if any term is found, False otherwise.
    """
    for term in terms:
        if term.lower() in transcript.lower():
            return True
    return False

def main():
    """
    Main function to determine if Karoline Leavitt said "sex" or its variations in the next White House press briefing.
    """
    current_date = datetime.now()
    if current_date > DEADLINE_DATE:
        print("recommendation: p1")  # No briefing by the deadline
        return

    transcript = fetch_white_house_briefing_videos()
    if check_term_in_transcript(transcript, EXPECTED_TERMS):
        print("recommendation: p2")  # Term was mentioned
    else:
        print("recommendation: p1")  # Term was not mentioned

if __name__ == "__main__":
    main()