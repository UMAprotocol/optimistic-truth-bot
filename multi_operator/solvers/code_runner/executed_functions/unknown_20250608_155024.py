import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
HLTV_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")

# Constants for the event
EVENT_DATE = "2025-06-08"
TEAM1 = "TYLOO"
TEAM2 = "Lynn Vision"
HLTV_EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# Headers for HTTP requests
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}

def get_match_result():
    """
    Fetches the match result from HLTV for the specified event and teams.
    """
    try:
        response = requests.get(HLTV_EVENT_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        matches = response.json()

        # Find the match between the specified teams
        for match in matches:
            if match['team1']['name'] == TEAM1 and match['team2']['name'] == TEAM2:
                if match['result']['team1'] > match['result']['team2']:
                    return "p2"  # TYLOO wins
                elif match['result']['team1'] < match['result']['team2']:
                    return "p1"  # Lynn Vision wins
                else:
                    return "p3"  # Tie or other unresolved outcome

        # If no match is found or the match is in the future
        return "p4"

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return "p4"  # Unable to resolve due to error

if __name__ == "__main__":
    # Ensure the current date is past the event date to check results
    if datetime.now() >= datetime.strptime(EVENT_DATE, "%Y-%m-%d"):
        result = get_match_result()
    else:
        result = "p4"  # Event has not occurred yet

    print(f"recommendation: {result}")