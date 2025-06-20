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
    "Athletics": "p2",
    "Angels": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Helper functions
def get_data(url, params=None):
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        try:
            # Fallback to proxy endpoint
            proxy_url = PROXY_ENDPOINT + url[len(PRIMARY_ENDPOINT):]
            response = requests.get(proxy_url, headers=HEADERS, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to retrieve data from both primary and proxy endpoints: {e}")
            return None

def resolve_market(game_date, home_team, away_team):
    date_str = game_date.strftime("%Y-%m-%d")
    games_today = get_data(f"{PRIMARY_ENDPOINT}/GamesByDate/{date_str}")

    if games_today:
        for game in games_today:
            if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
                if game["Status"] == "Final":
                    home_score = game["HomeTeamRuns"]
                    away_score = game["AwayTeamRuns"]
                    if home_score > away_score:
                        return RESOLUTION_MAP[home_team]
                    elif away_score > home_score:
                        return RESOLUTION_MAP[away_team]
                elif game["Status"] in ["Canceled", "Postponed"]:
                    return RESOLUTION_MAP["50-50"]
                else:
                    return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    game_date = datetime.strptime("2025-06-10 21:38", "%Y-%m-%d %H:%M")
    home_team = "Angels"
    away_team = "Athletics"
    result = resolve_market(game_date, home_team, away_team)
    print(f"recommendation: {result}")