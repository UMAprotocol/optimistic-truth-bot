import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants for the event
EVENT_DATE = "2025-06-12"
TEAM1 = "FaZe"  # Corresponds to p1
TEAM2 = "Aurora"  # Corresponds to p2
EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# Headers for HTTP requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_match_result():
    try:
        response = requests.get(EVENT_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Find the match between the specified teams
        for match in data.get('matches', []):
            if match['team1']['name'] == TEAM1 and match['team2']['name'] == TEAM2:
                if match['status'] == 'Finished':
                    if match['winner'] == TEAM1:
                        return "p1"
                    elif match['winner'] == TEAM2:
                        return "p2"
                elif match['status'] in ['Canceled', 'Postponed']:
                    return "p3"
        # If no specific match info is found, assume it's still scheduled
        return "p4"
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "p4"

if __name__ == "__main__":
    result = get_match_result()
    print(f"recommendation: {result}")