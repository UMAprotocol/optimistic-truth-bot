import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants - RESOLUTION MAPPING
RESOLUTION_MAP = {
    "Boston Red Sox": "p2",
    "St. Louis Cardinals": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

def fetch_game_data(date, home_team, away_team):
    """
    Fetches game data for the specified date and teams.
    """
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
                return game
        return None
    except requests.RequestException as e:
        logger.error(f"Failed to fetch game data: {e}")
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
            return RESOLUTION_MAP["Boston Red Sox"]
        else:
            return RESOLUTION_MAP["St. Louis Cardinals"]
    elif status == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]
    elif status == "Canceled":
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    # Hardcoded values extracted from the question
    date = "2025-04-04"
    home_team = "BOS"  # Boston Red Sox
    away_team = "STL"  # St. Louis Cardinals

    game = fetch_game_data(date, home_team, away_team)
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()