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
    "Angels": "p2",
    "Yankees": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_data(url, proxy=False):
    endpoint = PROXY_ENDPOINT if proxy else PRIMARY_ENDPOINT
    try:
        response = requests.get(f"{endpoint}{url}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if proxy:
            print("Proxy failed, trying primary endpoint.")
            return get_data(url, proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

def resolve_game(date, team1, team2):
    games_today = get_data(f"/GamesByDate/{date}")
    if games_today is None:
        return "Too early to resolve"

    for game in games_today:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                return RESOLUTION_MAP.get(winner, "50-50")
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "50-50"
            else:
                return "Too early to resolve"
    return "Too early to resolve"

if __name__ == "__main__":
    # Set the date of the game and the teams involved
    game_date = "2025-06-19"
    home_team = "Yankees"
    away_team = "Angels"

    # Resolve the game outcome
    result = resolve_game(game_date, home_team, away_team)
    print(f"recommendation: {RESOLUTION_MAP.get(result, 'p4')}")