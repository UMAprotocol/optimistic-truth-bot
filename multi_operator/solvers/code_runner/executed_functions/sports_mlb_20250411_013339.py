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
    "Knicks": "p2",  # Knicks win maps to p2
    "Pistons": "p1",  # Pistons win maps to p1
    "50-50": "p3",  # Canceled or no make-up game maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

logger = logging.getLogger(__name__)

def fetch_game_data():
    """
    Fetches game data for the Knicks vs Pistons game on the specified date.

    Returns:
        Game data dictionary or None if not found
    """
    date = "2025-04-10"
    home_team = "DET"  # Pistons abbreviation
    away_team = "NYK"  # Knicks abbreviation

    logger.info(f"Fetching game data for {away_team} @ {home_team} on {date}")

    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}?key={API_KEY}"
    logger.debug(f"Using API endpoint: {url}")

    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
                logger.info(f"Found matching game: {away_team} @ {home_team}")
                return game

        logger.warning(f"No matching game found between {away_team} and {home_team} on {date}.")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
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
        logger.info("No game data available, returning 'Too early to resolve'")
        return RESOLUTION_MAP["Too early to resolve"]

    status = game.get("Status")
    home_score = game.get("HomeTeamScore")
    away_score = game.get("AwayTeamScore")

    if status == "Final":
        if home_score > away_score:
            return RESOLUTION_MAP["Pistons"]
        elif away_score > home_score:
            return RESOLUTION_MAP["Knicks"]
    elif status == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]
    elif status == "Canceled":
        return RESOLUTION_MAP["50-50"]

    return RESOLUTION_MAP["Too early to resolve"]

def main():
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()