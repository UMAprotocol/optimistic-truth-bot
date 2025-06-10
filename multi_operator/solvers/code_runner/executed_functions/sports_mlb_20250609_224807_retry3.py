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
    "Braves": "p2",
    "Phillies": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_data(url, params=None):
    try:
        response = requests.get(PROXY_ENDPOINT + url, headers=HEADERS, params=params, timeout=10)
        if not response.ok:
            raise Exception("Proxy failed, trying primary endpoint.")
    except:
        response = requests.get(PRIMARY_ENDPOINT + url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
    return response.json()

def resolve_game(date, team1, team2):
    games_today = get_data(f"/GamesByDate/{date}")
    for game in games_today:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return RESOLUTION_MAP[game["HomeTeam"]]
                elif game["HomeTeamRuns"] < game["AwayTeamRuns"]:
                    return RESOLUTION_MAP[game["AwayTeam"]]
            elif game["Status"] in ["Canceled", "Postponed"]:
                return RESOLUTION_MAP["50-50"]
            return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    game_date = "2025-05-29"
    team1_key = "PHI"  # Phillies
    team2_key = "ATL"  # Braves
    recommendation = resolve_game(game_date, team1_key, team2_key)
    print(f"recommendation: {recommendation}")