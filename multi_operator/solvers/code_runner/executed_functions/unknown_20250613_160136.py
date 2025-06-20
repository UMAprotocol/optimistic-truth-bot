import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
HLTV_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")

# Constants for the event
EVENT_DATE = "2025-06-13"
TEAM1 = "Legacy"
TEAM2 = "FaZe"
EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# Headers for HTTP requests
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}

def get_match_result():
    """
    Fetches the match result from the HLTV API and determines the outcome based on the match result.
    """
    try:
        # Make a request to the HLTV API
        response = requests.get(EVENT_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Search for the specific match by date and teams
        for match in data.get('matches', []):
            if match['date'].startswith(EVENT_DATE) and {TEAM1, TEAM2} == {match['team1']['name'], match['team2']['name']}:
                if match['status'] == 'Finished':
                    winner = match['winner_team']['name']
                    if winner == TEAM1:
                        return "recommendation: p2"  # Legacy wins
                    elif winner == TEAM2:
                        return "recommendation: p1"  # FaZe wins
                elif match['status'] in ['Canceled', 'Postponed']:
                    return "recommendation: p3"  # Match canceled or postponed
                break
        return "recommendation: p3"  # No match found or unresolved status
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "recommendation: p3"  # Default to unknown/50-50 in case of error

if __name__ == "__main__":
    result = get_match_result()
    print(result)