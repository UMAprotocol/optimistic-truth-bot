import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
DATE = "2025-05-29"
TEAM1 = "Seattle Mariners"
TEAM2 = "Washington Nationals"
RESOLUTION_MAP = {
    TEAM1: "p1",  # Mariners win
    TEAM2: "p2",  # Nationals win
    "50-50": "p3",  # Game canceled or unresolved
    "Too early to resolve": "p4"  # Not enough data or future game
}

# API Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
BASE_URL = "https://api.sportsdata.io/v3/mlb/scores/json"

def get_games_by_date(date):
    url = f"{BASE_URL}/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def resolve_market(games, team1, team2):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                home_team_wins = game["HomeTeamRuns"] > game["AwayTeamRuns"]
                away_team_wins = game["AwayTeamRuns"] > game["HomeTeamRuns"]
                if home_team_wins:
                    return "recommendation: " + RESOLUTION_MAP[game["HomeTeam"]]
                elif away_team_wins:
                    return "recommendation: " + RESOLUTION_MAP[game["AwayTeam"]]
            elif game["Status"] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            elif game["Status"] == "Postponed":
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    games = get_games_by_date(DATE)
    if games:
        result = resolve_market(games, TEAM1, TEAM2)
    else:
        result = "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    print(result)