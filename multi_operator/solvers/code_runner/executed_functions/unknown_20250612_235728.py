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
TEAM1 = "G2"
TEAM2 = "paiN"
EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# Headers for HTTP requests
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}

def get_match_result():
    """
    Fetches the match result from the HLTV API and determines the outcome based on the match result.
    """
    try:
        response = requests.get(EVENT_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        match_data = response.json()

        # Check if the match is found and extract results
        for match in match_data.get('matches', []):
            if match['team1']['name'] == TEAM1 and match['team2']['name'] == TEAM2:
                if match['status'] == 'Finished':
                    if match['winner'] == TEAM1:
                        return "p2"  # G2 wins
                    elif match['winner'] == TEAM2:
                        return "p1"  # paiN wins
                elif match['status'] in ['Canceled', 'Postponed']:
                    return "p3"  # Match canceled or postponed
        # If no specific match info is found or match is still scheduled
        return "p3"  # Resolve as unknown/50-50 if no clear result is available

    except requests.RequestException as e:
        print(f"Error fetching match data: {e}")
        return "p3"  # Resolve as unknown/50-50 in case of error

if __name__ == "__main__":
    # Ensure the current date is not before the event date
    if datetime.now() < datetime.strptime(EVENT_DATE, "%Y-%m-%d"):
        print("recommendation: p4")  # Too early / in-progress
    else:
        result = get_match_result()
        print(f"recommendation: {result}")