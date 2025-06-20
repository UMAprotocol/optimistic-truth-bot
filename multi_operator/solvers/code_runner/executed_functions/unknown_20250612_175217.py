import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
HLTV_BASE_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
MATCH_DATE = "2025-06-12"
TEAM1 = "FaZe"
TEAM2 = "Aurora"
TIMEOUT = 10

# Headers for HTTP requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_match_result():
    try:
        # Fetch data from HLTV
        response = requests.get(HLTV_BASE_URL, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()

        # Find the match data
        for match in data.get('matches', []):
            if match['date'].startswith(MATCH_DATE) and {TEAM1, TEAM2} == {match['team1']['name'], match['team2']['name']}:
                if match['status'] == 'Finished':
                    winner = match['winner']['name']
                    if winner == TEAM1:
                        return "p1"
                    elif winner == TEAM2:
                        return "p2"
                elif match['status'] in ['Canceled', 'Postponed']:
                    return "p3"
        # If no match is found or it is not yet finished
        return "p4"
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "p4"

if __name__ == "__main__":
    result = get_match_result()
    print(f"recommendation: {result}")