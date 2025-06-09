import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
HLTV_EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
MATCH_DATE = "2025-06-05"
MATCH_TIME = "11:00 AM ET"
TEAM1 = "Imperial"
TEAM2 = "Legacy"
RESOLUTION_MAP = {
    TEAM1: "p2",
    TEAM2: "p1",
    "tie": "p3",
    "unknown": "p3"
}

# Load API key from environment
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def fetch_match_results():
    """Fetch match results from HLTV."""
    try:
        response = requests.get(HLTV_EVENT_URL, headers=HEADERS)
        response.raise_for_status()
        matches = response.json()
        for match in matches:
            if match['team1']['name'] == TEAM1 and match['team2']['name'] == TEAM2:
                if match['date'] == MATCH_DATE and match['time'] == MATCH_TIME:
                    if match['result']['team1'] > match['result']['team2']:
                        return RESOLUTION_MAP[TEAM1]
                    elif match['result']['team1'] < match['result']['team2']:
                        return RESOLUTION_MAP[TEAM2]
                    else:
                        return RESOLUTION_MAP["tie"]
        return RESOLUTION_MAP["unknown"]
    except requests.RequestException as e:
        print(f"Error fetching match results: {e}")
        return RESOLUTION_MAP["unknown"]

if __name__ == "__main__":
    recommendation = fetch_match_results()
    print(f"recommendation: {recommendation}")