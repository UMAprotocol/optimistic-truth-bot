import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
HLTV_EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
MATCH_DATE = "2025-06-12"
MATCH_TIME = "14:45"
TEAM_1 = "Liquid"
TEAM_2 = "Lynn Vision"
TIMEOUT = 10

# Load API key from environment
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def fetch_match_data():
    try:
        response = requests.get(HLTV_EVENT_URL, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        matches = response.json()
        for match in matches:
            if match['team1']['name'] == TEAM_1 and match['team2']['name'] == TEAM_2:
                match_date = datetime.strptime(match['date'], "%Y-%m-%d %H:%M:%S")
                if match_date.strftime("%Y-%m-%d") == MATCH_DATE and match_date.strftime("%H:%M") == MATCH_TIME:
                    return match
        return None
    except requests.RequestException as e:
        print(f"Error fetching match data: {e}")
        return None

def resolve_market(match):
    if not match:
        print("Match data not found or match does not exist.")
        return "recommendation: p3"
    
    if match['status'] == 'Finished':
        if match['winner'] == TEAM_1:
            return "recommendation: p2"
        elif match['winner'] == TEAM_2:
            return "recommendation: p1"
    elif match['status'] in ['Canceled', 'Postponed']:
        return "recommendation: p3"
    
    return "recommendation: p3"

if __name__ == "__main__":
    match_data = fetch_match_data()
    result = resolve_market(match_data)
    print(result)