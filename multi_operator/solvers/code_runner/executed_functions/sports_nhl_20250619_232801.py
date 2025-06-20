import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
EVENT_DATE = "2025-06-19"
MATCH_TIME = "19:30:00"
TEAM1 = "Spirit"  # Corresponds to p2 in resolution conditions
TEAM2 = "MOUZ"    # Corresponds to p1 in resolution conditions
RESOLUTION_MAP = {
    "Spirit": "p2",
    "MOUZ": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Helper functions
def get_match_result():
    # Construct the date and time for the match
    match_datetime = datetime.strptime(f"{EVENT_DATE} {MATCH_TIME}", "%Y-%m-%d %H:%M:%S")
    current_datetime = datetime.utcnow()

    # Check if the match is yet to occur
    if current_datetime < match_datetime:
        return RESOLUTION_MAP["Too early to resolve"]

    # Check if the match is delayed beyond the allowed date
    if current_datetime > match_datetime + timedelta(days=9):
        return RESOLUTION_MAP["50-50"]

    # Fetch match data from HLTV
    try:
        response = requests.get("https://www.hltv.org/events/7902/blasttv-austin-major-2025")
        response.raise_for_status()
        match_data = response.json()

        # Find the specific match
        for match in match_data:
            if match['team1']['name'] == TEAM1 and match['team2']['name'] == TEAM2:
                if match['winner'] == TEAM1:
                    return RESOLUTION_MAP[TEAM1]
                elif match['winner'] == TEAM2:
                    return RESOLUTION_MAP[TEAM2]
                else:
                    return RESOLUTION_MAP["50-50"]
    except requests.RequestException as e:
        print(f"Error fetching match data: {e}")
        return RESOLUTION_MAP["50-50"]

    return RESOLUTION_MAP["50-50"]

# Main execution
if __name__ == "__main__":
    result = get_match_result()
    print("recommendation:", result)