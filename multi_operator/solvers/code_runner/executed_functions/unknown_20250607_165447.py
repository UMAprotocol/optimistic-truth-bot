import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
HLTV_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")

# Constants for the event
EVENT_DATE = "2025-06-07"
TEAM_1 = "3DMAX"
TEAM_2 = "BetBoom"
EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}

def get_match_result():
    """
    Fetches the match result from the HLTV API and determines the outcome based on the match result.
    """
    if not HLTV_API_KEY:
        raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

    try:
        response = requests.get(EVENT_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        match_data = response.json()

        # Check if the match is found and extract results
        for match in match_data.get('matches', []):
            if match['team1']['name'] == TEAM_1 and match['team2']['name'] == TEAM_2:
                if match['status'] == 'Finished':
                    if match['winner'] == TEAM_1:
                        return "p2"  # 3DMAX wins
                    elif match['winner'] == TEAM_2:
                        return "p1"  # BetBoom wins
                elif match['status'] in ['Canceled', 'Postponed']:
                    return "p3"  # Match canceled or postponed
        # If no specific match info is found, assume it's still upcoming
        return "p3"  # Default to unknown/50-50 if no information is available

    except requests.RequestException as e:
        print(f"Error fetching match data: {e}")
        return "p3"  # Default to unknown/50-50 in case of request failure

if __name__ == "__main__":
    # Ensure the current date is not before the event date
    current_date = datetime.now().strftime("%Y-%m-%d")
    if current_date < EVENT_DATE:
        print("recommendation: p4")  # Too early / in-progress
    else:
        result = get_match_result()
        print(f"recommendation: {result}")