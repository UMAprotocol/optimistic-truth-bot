import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
EVENT_DATE = "2025-06-05"
TEAM1 = "Imperial"
TEAM2 = "Legacy"
HLTV_EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# Load API key from environment
HLTV_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not HLTV_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}

def get_match_result():
    try:
        # Request data from HLTV
        response = requests.get(HLTV_EVENT_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        matches = response.json()

        # Find the specific match
        for match in matches:
            if match['date'] == EVENT_DATE and TEAM1 in match['teams'] and TEAM2 in match['teams']:
                if match['status'] == 'Finished':
                    winner = match['winner']
                    if winner == TEAM1:
                        return "p2"  # Imperial wins
                    elif winner == TEAM2:
                        return "p1"  # Legacy wins
                elif match['status'] in ['Canceled', 'Postponed']:
                    return "p3"  # 50-50
        return "p3"  # Default to 50-50 if no match found or in case of tie

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return "p3"  # Default to 50-50 in case of error

if __name__ == "__main__":
    result = get_match_result()
    print(f"recommendation: {result}")