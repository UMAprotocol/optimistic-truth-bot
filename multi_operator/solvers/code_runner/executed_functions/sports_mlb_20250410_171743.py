import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Check if API key is available
if not API_KEY:
    raise ValueError(
        "SPORTS_DATA_IO_MLB_API_KEY not found in environment variables. "
        "Please add it to your .env file."
    )

# Constants - RESOLUTION MAPPING
RESOLUTION_MAP = {
    "Los Angeles Angels": "p2",  # Los Angeles Angels win maps to p2
    "Tampa Bay Rays": "p1",      # Tampa Bay Rays win maps to p1
    "50-50": "p3",               # Canceled or no make-up game maps to p3
    "Too early to resolve": "p4" # Incomplete data maps to p4
}

logger = logging.getLogger(__name__)

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
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
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
            return RESOLUTION_MAP["Los Angeles Angels"]
        else:
            return RESOLUTION_MAP["Tampa Bay Rays"]
    elif status == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif status == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    date = "2025-04-09"
    home_team = "LAA"  # Los Angeles Angels
    away_team = "TBR"  # Tampa Bay Rays

    game = fetch_game_data(date, home_team, away_team)
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()