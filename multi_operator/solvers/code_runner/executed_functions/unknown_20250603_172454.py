import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
HLTV_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")

# Constants for the event
EVENT_DATE = "2025-06-03"
TEAM1 = "B8"
TEAM2 = "Imperial"
MATCH_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# Headers for HTTP requests
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}

def get_match_result():
    """
    Fetches the match result from the HLTV API and determines the outcome based on the match result.
    """
    try:
        response = requests.get(MATCH_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        match_data = response.json()

        # Find the specific match by date and teams
        for match in match_data:
            if match['date'].startswith(EVENT_DATE) and {TEAM1, TEAM2} == {match['team1']['name'], match['team2']['name']}:
                if match['status'] == 'Finished':
                    winner = match['winner']['name']
                    if winner == TEAM1:
                        return "recommendation: p2"  # B8 wins
                    elif winner == TEAM2:
                        return "recommendation: p1"  # Imperial wins
                elif match['status'] in ['Canceled', 'Postponed']:
                    return "recommendation: p3"  # 50-50
        return "recommendation: p3"  # Default to 50-50 if no match found or in case of tie

    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return "recommendation: p3"  # Resolve as 50-50 in case of error

if __name__ == "__main__":
    result = get_match_result()
    print(result)