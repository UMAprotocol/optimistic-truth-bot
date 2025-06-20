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
    "Cardinals": "p2",
    "White Sox": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_data(url, proxy=False):
    endpoint = PROXY_ENDPOINT if proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if proxy:
            print(f"Proxy failed, trying primary endpoint: {e}")
            return get_data(url, proxy=False)
        else:
            print(f"Error accessing API: {e}")
            return None

def find_game(date, team1, team2):
    games = get_data(f"/GamesByDate/{date}")
    if games:
        for game in games:
            teams = {game["HomeTeam"], game["AwayTeam"]}
            if team1 in teams and team2 in teams:
                return game
    return None

def resolve_market(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game["Status"] == "Final":
        if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
            winner = game["HomeTeam"]
        else:
            winner = game["AwayTeam"]
        return RESOLUTION_MAP[winner]
    elif game["Status"] in ["Canceled", "Postponed"]:
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    game_date = "2025-06-18"
    team1 = "STL"
    team2 = "CWS"
    game = find_game(game_date, team1, team2)
    recommendation = resolve_market(game)
    print(f"recommendation: {recommendation}")