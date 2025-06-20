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
TOURNAMENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# Headers for HTTP requests
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}

def get_match_result():
    """
    Fetches the match result from the HLTV API and determines the outcome based on the match status and scores.
    """
    try:
        response = requests.get(TOURNAMENT_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        matches = response.json()

        # Find the specific match by date and teams
        for match in matches:
            if (match['date'].startswith(EVENT_DATE) and
                match['team1']['name'] == TEAM1 and
                match['team2']['name'] == TEAM2):
                
                if match['status'] == 'Finished':
                    if match['team1']['score'] > match['team2']['score']:
                        return "recommendation: p1"  # TEAM1 wins
                    elif match['team1']['score'] < match['team2']['score']:
                        return "recommendation: p2"  # TEAM2 wins
                    else:
                        return "recommendation: p3"  # Tie
                elif match['status'] in ['Canceled', 'Postponed']:
                    return "recommendation: p3"  # 50-50 due to cancellation or postponement
                else:
                    return "recommendation: p3"  # 50-50 for any other non-final status

        return "recommendation: p3"  # Default to 50-50 if no match is found or other conditions apply

    except requests.RequestException as e:
        print(f"Failed to retrieve data: {e}")
        return "recommendation: p3"  # Default to 50-50 on failure

if __name__ == "__main__":
    result = get_match_result()
    print(result)