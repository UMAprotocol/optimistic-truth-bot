import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}
RESOLUTION_MAP = {
    "EDM": "p2",  # Edmonton Oilers
    "LAK": "p1",  # Los Angeles Kings
    "50-50": "p3",
    "Too early to resolve": "p4",
}
END_DATE = datetime(2025, 5, 20, 23, 59)

# Helper functions
def get_json_response(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def check_team_advance(team_key):
    current_date = datetime.now()
    if current_date > END_DATE:
        return "50-50"
    
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/Standings/{current_date.year}"
    standings = get_json_response(url, HEADERS)
    if standings is None:
        return "Too early to resolve"
    
    for team in standings:
        if team["Key"] == team_key and team["PlayoffSeeding"] > 0:
            return RESOLUTION_MAP[team_key]
    return "Too early to resolve"

# Main execution
if __name__ == "__main__":
    result_oilers = check_team_advance("EDM")
    result_kings = check_team_advance("LAK")
    
    if result_oilers == "p2" and result_kings != "p2":
        print("recommendation: p2")  # Oilers advance
    elif result_kings == "p1" and result_oilers != "p2":
        print("recommendation: p1")  # Kings advance
    elif result_oilers == "50-50" or result_kings == "50-50":
        print("recommendation: p3")  # Series canceled or postponed
    else:
        print("recommendation: p4")  # Too early to resolve or data unavailable