import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants - RESOLUTION MAPPING
RESOLUTION_MAP = {
    "Milwaukee Brewers": "p2",  # Milwaukee Brewers win maps to p2
    "Colorado Rockies": "p1",   # Colorado Rockies win maps to p1
    "50-50": "p3",              # Canceled or no make-up game maps to p3
    "Too early to resolve": "p4"  # Incomplete data maps to p4
}

def fetch_game_data():
    """
    Fetches game data for the Milwaukee Brewers vs. Colorado Rockies game on April 10, 2025.

    Returns:
        Game data dictionary or None if not found
    """
    date = "2025-04-10"
    home_team = "MIL"  # Milwaukee Brewers abbreviation
    away_team = "COL"  # Colorado Rockies abbreviation
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
                return game
        return None

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.

    Args:
        game: Game data dictionary

    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]

    status = game.get("Status")
    if status == "Final":
        home_score = game.get("HomeTeamRuns")
        away_score = game.get("AwayTeamRuns")
        if home_score > away_score:
            return RESOLUTION_MAP["Milwaukee Brewers"]
        else:
            return RESOLUTION_MAP["Colorado Rockies"]
    elif status == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif status == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()