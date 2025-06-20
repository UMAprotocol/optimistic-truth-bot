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
TEAM1 = "3DMAX"
TEAM2 = "G2"
EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# Headers for HTTP requests
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}

def fetch_event_results():
    """
    Fetches the results of the BLAST.tv Austin Major: G2 vs. 3DMAX match from HLTV.
    """
    try:
        response = requests.get(EVENT_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Find the specific match data
        for match in data.get('matches', []):
            if match['team1']['name'] == TEAM1 and match['team2']['name'] == TEAM2:
                if match['date'][:10] == EVENT_DATE:
                    return match
        return None
    except requests.RequestException as e:
        print(f"Error fetching event results: {e}")
        return None

def determine_outcome(match_data):
    """
    Determines the outcome of the match based on the fetched data.
    """
    if not match_data:
        return "p3"  # Assume 50-50 if no data is found or match is not on the expected date

    if match_data['status'] in ['Postponed', 'Canceled']:
        return "p3"  # 50-50 for postponed or canceled matches

    winner = match_data['winner']['name']
    if winner == TEAM1:
        return "p1"  # 3DMAX wins
    elif winner == TEAM2:
        return "p2"  # G2 wins
    else:
        return "p3"  # 50-50 for any other unexpected outcome

if __name__ == "__main__":
    match_data = fetch_event_results()
    recommendation = determine_outcome(match_data)
    print(f"recommendation: {recommendation}")