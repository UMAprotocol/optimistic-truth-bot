import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
HLTV_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")

# Constants for the event
EVENT_DATE = "2025-06-12"
TEAM1 = "Spirit"
TEAM2 = "Lynn Vision"
TOURNAMENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}

def get_match_result():
    """
    Fetches the match result from the HLTV API and determines the outcome based on the match result.
    """
    if not HLTV_API_KEY:
        raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

    try:
        response = requests.get(TOURNAMENT_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        matches = response.json()

        # Find the specific match by date and teams
        for match in matches:
            if (match['date'].startswith(EVENT_DATE) and
                match['team1']['name'] == TEAM1 and
                match['team2']['name'] == TEAM2):
                if match['winner'] == TEAM1:
                    return "p2"  # Spirit wins
                elif match['winner'] == TEAM2:
                    return "p1"  # Lynn Vision wins
                else:
                    return "p3"  # Tie or no clear winner

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from HLTV: {e}")
        return "p3"  # Resolve as 50-50 in case of data fetch failure

    # If no match is found or data is inconclusive
    return "p3"

if __name__ == "__main__":
    result = get_match_result()
    print(f"recommendation: {result}")