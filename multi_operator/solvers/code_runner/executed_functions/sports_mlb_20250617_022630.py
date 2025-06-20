import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants
GAME_DATE = "2025-06-16"
TEAM1 = "New York Yankees"
TEAM2 = "Los Angeles Angels"

# Resolution map
RESOLUTION_MAP = {
    TEAM1: "p1",
    TEAM2: "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def find_game(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{formatted_date}"
    games = get(url)
    if games:
        for game in games:
            if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
                return game
    return None

def resolve_market(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game["Status"] == "Final":
        home_runs = game["HomeTeamRuns"]
        away_runs = game["AwayTeamRuns"]
        if home_runs > away_runs:
            winner = game["HomeTeam"]
        else:
            winner = game["AwayTeam"]
        return RESOLUTION_MAP.get(winner, "50-50")
    elif game["Status"] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game["Status"] == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    game = find_game(GAME_DATE, TEAM1, TEAM2)
    recommendation = resolve_market(game)
    print(f"recommendation: {recommendation}")