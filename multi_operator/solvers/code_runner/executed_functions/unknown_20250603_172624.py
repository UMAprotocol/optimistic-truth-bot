import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
HLTV_API_KEY = os.getenv("HLTV_API_KEY")

# Constants
EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
MATCH_DATE = datetime(2025, 6, 3, 12, 15)  # 12:15 PM ET, June 3, 2025
CURRENT_TIME = datetime.utcnow()

# Resolution map
RESOLUTION_MAP = {
    "B8": "p2",
    "Imperial": "p1",
    "tie": "p3",
    "unknown": "p4"
}

def fetch_match_result():
    headers = {"Authorization": f"Bearer {HLTV_API_KEY}"}
    try:
        response = requests.get(EVENT_URL, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        for match in data.get('matches', []):
            if match['team1']['name'] == "B8" and match['team2']['name'] == "Imperial":
                if match['status'] == "Finished":
                    winner = match['winner_team']['name']
                    return RESOLUTION_MAP.get(winner, "p3")
                elif match['status'] in ["Canceled", "Postponed"]:
                    return "p3"
        return "p4"  # Match not found or not yet played
    except requests.exceptions.RequestException as e:
        print(f"Error fetching match result: {e}")
        return "p4"  # Default to unknown if there's an error

def main():
    if CURRENT_TIME < MATCH_DATE:
        print("recommendation: p4")  # Match has not occurred yet
    else:
        result = fetch_match_result()
        print(f"recommendation: {result}")

if __name__ == "__main__":
    main()