import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants - RESOLUTION MAPPING
RESOLUTION_MAP = {
    "Pittsburgh Pirates": "p2",  # Pittsburgh Pirates win maps to p2
    "St. Louis Cardinals": "p1",  # St. Louis Cardinals win maps to p1
    "50-50": "p3",  # Canceled or postponed game maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

def fetch_game_data(date, home_team, away_team):
    """
    Fetches game data for the specified date and teams.
    """
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
                return game
    return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]

    status = game.get("Status")
    if status == "Final":
        home_score = game.get("HomeTeamRuns")
        away_score = game.get("AwayTeamRuns")
        if home_score > away_score:
            return RESOLUTION_MAP["Pittsburgh Pirates"]
        else:
            return RESOLUTION_MAP["St. Louis Cardinals"]
    elif status in ["Postponed", "Canceled"]:
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    date = "2025-04-09"
    home_team = "PIT"  # Pittsburgh Pirates abbreviation
    away_team = "STL"  # St. Louis Cardinals abbreviation

    game = fetch_game_data(date, home_team, away_team)
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()