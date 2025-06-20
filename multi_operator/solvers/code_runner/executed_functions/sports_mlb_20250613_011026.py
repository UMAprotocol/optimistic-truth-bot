import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
DEBATE_DATE = "2025-06-12"
DEBATE_TIME = "19:00:00"
TIMEZONE = "ET"
TERM = "Subway"
MIN_COUNT = 5

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Function to check the occurrence of the term in the debate
def check_term_occurrence(video_url):
    # This is a placeholder for the actual implementation which would involve processing the video
    # to check for the term occurrence. This should ideally be replaced with an actual video processing logic.
    response = requests.get(video_url, headers=HEADERS)
    if response.status_code == 200:
        # Assuming the response contains a transcript where each line represents a candidate's speech
        transcript = response.text.split('\n')
        term_count = sum(line.lower().count(TERM.lower()) for line in transcript if "candidate" in line.lower())
        return term_count >= MIN_COUNT
    else:
        raise Exception("Failed to fetch or process the video")

# Main function to determine the outcome based on the term occurrence
def resolve_market():
    # Placeholder for the actual video URL of the debate
    video_url = "http://example.com/debate_video"
    try:
        if check_term_occurrence(video_url):
            return "recommendation: p2"  # Yes, term said 5+ times
        else:
            return "recommendation: p1"  # No, term not said 5+ times
    except Exception as e:
        print(f"Error: {str(e)}")
        return "recommendation: p3"  # Unknown/50-50 due to error

# Run the resolution function
if __name__ == "__main__":
    result = resolve_market()
    print(result)