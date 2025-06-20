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
TEAM1 = "G2"
TEAM2 = "Aurora"
EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}

def get_match_result():
    """
    Fetches the match result from the HLTV API and determines the outcome based on the match result.
    """
    try:
        response = requests.get(EVENT_URL, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            match_data = response.json()
            for match in match_data.get('matches', []):
                if match['date'].startswith(EVENT_DATE) and {TEAM1, TEAM2} == {match['team1']['name'], match['team2']['name']}:
                    if match['status'] == 'Finished':
                        winner = match['winner_team']['name']
                        if winner == TEAM1:
                            return "p1"
                        elif winner == TEAM2:
                            return "p2"
                    elif match['status'] in ['Canceled', 'Postponed']:
                        return "p3"
            return "p3"  # Default to 50-50 if no specific match info is found
        else:
            print(f"Failed to fetch data: {response.status_code} {response.reason}")
            return "p3"
    except requests.RequestException as e:
        print(f"Error fetching match data: {e}")
        return "p3"

if __name__ == "__main__":
    recommendation = get_match_result()
    print(f"recommendation: {recommendation}")