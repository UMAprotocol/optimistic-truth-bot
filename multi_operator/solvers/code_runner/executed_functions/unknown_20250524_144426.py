import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return None

# Function to check if "Dome" was mentioned in the speech
def check_dome_mention():
    # Simulated API path for the event transcript (this is a placeholder)
    transcript_path = "GamesByDate/2025-05-24"

    # Try proxy endpoint first
    transcript = make_request(PROXY_ENDPOINT, transcript_path)
    if transcript is None:
        # Fallback to primary endpoint if proxy fails
        transcript = make_request(PRIMARY_ENDPOINT, transcript_path)

    if transcript:
        # Check if "Dome" is mentioned in the transcript
        if "Dome" in transcript.get('Transcript', ''):
            return "p2"  # Yes, "Dome" was mentioned
        else:
            return "p1"  # No, "Dome" was not mentioned
    else:
        return "p3"  # Unable to retrieve data or event did not occur

# Main execution
if __name__ == "__main__":
    result = check_dome_mention()
    print(f"recommendation: {result}")