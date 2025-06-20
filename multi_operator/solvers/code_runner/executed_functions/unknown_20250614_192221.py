import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
HLTV_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")

# Constants for the event
EVENT_DATE = "2025-06-14"
TEAM1 = "FaZe"
TEAM2 = "The MongolZ"
TOURNAMENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# Headers for HTTP requests
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}

def get_match_result():
    """
    Fetches the match result from the HLTV API and determines the outcome based on the match result.
    """
    try:
        response = requests.get(TOURNAMENT_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        matches = response.json()

        # Find the specific match by date and teams
        for match in matches:
            if (match['date'].startswith(EVENT_DATE) and
                TEAM1 in match['teams'] and
                TEAM2 in match['teams']):
                if match['result'] == 'canceled' or match['result'] == 'postponed':
                    return "p3"  # Match canceled or postponed
                elif match['winner'] == TEAM1:
                    return "p1"  # Team1 wins
                elif match['winner'] == TEAM2:
                    return "p2"  # Team2 wins
                else:
                    return "p3"  # It's a tie or something unexpected
        return "p3"  # No match found or no clear result
    except requests.RequestException as e:
        print(f"Error fetching match data: {e}")
        return "p3"  # Assume unknown result in case of error

if __name__ == "__main__":
    result = get_match_result()
    print(f"recommendation: {result}")