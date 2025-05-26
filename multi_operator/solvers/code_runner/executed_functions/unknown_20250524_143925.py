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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check if Trump said "Fire" in the speech
def check_speech_for_term(date):
    path = f"/scores/json/GamesByDate/{date}"
    # Try proxy endpoint first
    data = make_request(PROXY_ENDPOINT, path)
    if data is None:
        # Fallback to primary endpoint
        data = make_request(PRIMARY_ENDPOINT, path)
    
    if data:
        for game in data:
            if "West Point" in game['Stadium']['Name']:
                # Assuming the speech text or summary is available in the 'Summary' field
                if 'fire' in game.get('Summary', '').lower():
                    return "p2"  # Yes, term "Fire" was said
        return "p1"  # No, term "Fire" was not said
    return "p3"  # Unknown or data not available

# Main execution
if __name__ == "__main__":
    event_date = "2025-05-24"
    result = check_speech_for_term(event_date)
    print(f"recommendation: {result}")