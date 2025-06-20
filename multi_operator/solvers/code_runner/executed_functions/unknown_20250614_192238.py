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
            if (match['date'] == EVENT_DATE and
                TEAM1 in match['teams'] and
                TEAM2 in match['teams']):
                if match['status'] == 'completed':
                    winner = match['winner']
                    if winner == TEAM1:
                        return "p1"  # FaZe wins
                    elif winner == TEAM2:
                        return "p2"  # The MongolZ wins
                elif match['status'] in ['canceled', 'postponed']:
                    return "p3"  # Match canceled or postponed
        return "p3"  # No match found or match not completed
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "p3"  # Assume 50-50 if there is an error

if __name__ == "__main__":
    result = get_match_result()
    print(f"recommendation: {result}")