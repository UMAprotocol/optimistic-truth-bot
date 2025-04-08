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
    "New York Yankees": "p1",
    "Pittsburgh Pirates": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

logger = logging.getLogger(__name__)

def fetch_game_data():
    """
    Fetches game data for the specified date and teams.
    """
    date = "2025-04-06"
    home_team = "PIT"
    away_team = "NYY"
    logger.info(f"Fetching game data for {away_team} @ {home_team} on {date}")

    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"
    logger.debug(f"Using API endpoint: {url}")

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
    if status in ["Scheduled", "InProgress"]:
        return RESOLUTION_MAP["Too early to resolve"]
    elif status in ["Postponed", "Canceled"]:
        return RESOLUTION_MAP["50-50"]
    elif status == "Final":
        home_score = game.get("HomeTeamRuns")
        away_score = game.get("AwayTeamRuns")
        if home_score > away_score:
            return RESOLUTION_MAP["Pittsburgh Pirates"]
        elif away_score > home_score:
            return RESOLUTION_MAP["New York Yankees"]
        else:
            return RESOLUTION_MAP["50-50"]

    return RESOLUTION_MAP["Too early to resolve"]

def main():
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()