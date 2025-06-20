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
TEAM1 = "Liquid"
TEAM2 = "The MongolZ"
EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}

def get_match_result():
    """
    Fetches the match result from the HLTV API and determines the outcome based on the match result.
    """
    try:
        # Make the API request
        response = requests.get(EVENT_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Check for match data
        for match in data.get('matches', []):
            if match['team1']['name'] == TEAM1 and match['team2']['name'] == TEAM2:
                if match['status'] == 'Finished':
                    if match['winner'] == TEAM1:
                        return "p1"  # Team1 wins
                    elif match['winner'] == TEAM2:
                        return "p2"  # Team2 wins
                elif match['status'] in ['Canceled', 'Postponed']:
                    return "p3"  # Match canceled or postponed
        return "p3"  # Default to 50-50 if no conclusive result is found

    except requests.RequestException as e:
        print(f"Error fetching match data: {e}")
        return "p3"  # Resolve as 50-50 in case of error

if __name__ == "__main__":
    result = get_match_result()
    print(f"recommendation: {result}")