import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
HLTV_EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
MATCH_DATE = "2025-06-15"
TEAM1 = "Virtus.pro"
TEAM2 = "paiN"
TIMEOUT = 10

# Load API key from environment
HLTV_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not HLTV_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Headers for HTTP requests
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}

def get_match_result():
    try:
        response = requests.get(HLTV_EVENT_URL, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        matches = response.json()

        # Find the specific match by date and teams
        for match in matches:
            if match['date'] == MATCH_DATE and {TEAM1, TEAM2} == {match['team1']['name'], match['team2']['name']}:
                if match['status'] == 'Finished':
                    winner = match['winner']['name']
                    if winner == TEAM1:
                        return "p1"
                    elif winner == TEAM2:
                        return "p2"
                elif match['status'] in ['Canceled', 'Postponed']:
                    return "p3"
        return "p3"  # Default to 50-50 if no match found or in case of tie
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return "p3"  # Resolve as 50-50 in case of network or data fetch issues

if __name__ == "__main__":
    result = get_match_result()
    print(f"recommendation: {result}")