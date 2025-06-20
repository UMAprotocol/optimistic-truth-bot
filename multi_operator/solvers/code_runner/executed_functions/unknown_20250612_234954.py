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
TOURNAMENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}

def get_match_result():
    """
    Fetches the match result from the HLTV API and determines the outcome based on the match result.
    """
    if not HLTV_API_KEY:
        print("API key is missing.")
        return "recommendation: p4"

    try:
        response = requests.get(TOURNAMENT_URL, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            matches = response.json()
            for match in matches:
                if (match['team1']['name'] == TEAM1 and match['team2']['name'] == TEAM2) or \
                   (match['team1']['name'] == TEAM2 and match['team2']['name'] == TEAM1):
                    if match['date'][:10] == EVENT_DATE:
                        if match['status'] == 'Finished':
                            winner = match['winner']['name']
                            if winner == TEAM1:
                                return "recommendation: p1"
                            elif winner == TEAM2:
                                return "recommendation: p2"
                        elif match['status'] in ['Canceled', 'Postponed']:
                            return "recommendation: p3"
                        else:
                            return "recommendation: p4"
            return "recommendation: p4"
        else:
            print(f"Failed to fetch data: {response.status_code}")
            return "recommendation: p4"
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "recommendation: p4"

if __name__ == "__main__":
    result = get_match_result()
    print(result)