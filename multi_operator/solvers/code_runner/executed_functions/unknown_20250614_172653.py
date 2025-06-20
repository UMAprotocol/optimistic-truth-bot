import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
HLTV_EVENT_ID = "7902"
MATCH_DATE = "2025-06-14"
TEAM_3DMAX = "3DMAX"
TEAM_PAIN = "paiN"

# API Configuration
HLTV_BASE_URL = "https://www.hltv.org/events"
HLTV_PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/hltv-proxy"

# Function to fetch match data
def fetch_match_data():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        # Try fetching via proxy first
        response = requests.get(f"{HLTV_PROXY_URL}/{HLTV_EVENT_ID}/matches", headers=headers, timeout=10)
        if not response.ok:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(f"{HLTV_BASE_URL}/{HLTV_EVENT_ID}/matches", headers=headers, timeout=10)
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to determine the outcome of the match
def determine_outcome(matches):
    for match in matches:
        if match['team1']['name'] == TEAM_3DMAX and match['team2']['name'] == TEAM_PAIN:
            if match['date'][:10] == MATCH_DATE:
                if match['result']['team1'] > match['result']['team2']:
                    return "recommendation: p1"  # 3DMAX wins
                elif match['result']['team1'] < match['result']['team2']:
                    return "recommendation: p2"  # paiN wins
                else:
                    return "recommendation: p3"  # Tie or other unresolved outcome
    return "recommendation: p3"  # No match found or other unresolved outcome

# Main execution function
def main():
    matches = fetch_match_data()
    if matches:
        outcome = determine_outcome(matches)
        print(outcome)
    else:
        print("recommendation: p3")  # Unable to fetch data or other unresolved outcome

if __name__ == "__main__":
    main()