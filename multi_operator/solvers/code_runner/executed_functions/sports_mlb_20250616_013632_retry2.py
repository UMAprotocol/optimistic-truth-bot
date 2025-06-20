import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not MLB_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": MLB_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map
RESOLUTION_MAP = {
    "Giants": "p2",
    "Dodgers": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_data(url, params=None):
    try:
        response = requests.get(PROXY_ENDPOINT + url, headers=HEADERS, params=params, timeout=10)
        if not response.ok:
            response = requests.get(PRIMARY_ENDPOINT + url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def resolve_market(date_str):
    games = get_data(f"/GamesByDate/{date_str}")
    if not games:
        return RESOLUTION_MAP["Too early to resolve"]

    for game in games:
        if game['HomeTeam'] == 'SF' and game['AwayTeam'] == 'LAD' or game['HomeTeam'] == 'LAD' and game['AwayTeam'] == 'SF':
            if game['Status'] == 'Final':
                home_runs = game['HomeTeamRuns']
                away_runs = game['AwayTeamRuns']
                if home_runs > away_runs:
                    return RESOLUTION_MAP[game['HomeTeam']]
                else:
                    return RESOLUTION_MAP[game['AwayTeam']]
            elif game['Status'] == 'Canceled':
                return RESOLUTION_MAP["50-50"]
            elif game['Status'] == 'Postponed':
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    game_date = "2025-06-15"
    print("recommendation:", resolve_market(game_date))