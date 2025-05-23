import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants - RESOLUTION MAPPING using team names
RESOLUTION_MAP = {
    "Pittsburgh Pirates": "p2",  # Pittsburgh Pirates win maps to p2
    "Los Angeles Angels": "p1",  # Los Angeles Angels win maps to p1
    "50-50": "p3",  # Canceled or no make-up game maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def fetch_game_data(date):
    """
    Fetches game data for the specified date.

    Args:
        date: Game date in YYYY-MM-DD format

    Returns:
        Game data dictionary or None if not found
    """
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"
    logger.info(f"Fetching game data for date: {date}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        # Find the specific game between Pittsburgh Pirates and Los Angeles Angels
        for game in games:
            if (game['HomeTeam'] == "PIT" and game['AwayTeam'] == "LAA") or (game['HomeTeam'] == "LAA" and game['AwayTeam'] == "PIT"):
                logger.info(f"Found game: {game['GameID']}")
                return game
        logger.warning("No matching game found.")
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
    home_team = game.get("HomeTeam")
    away_team = game.get("AwayTeam")
    home_score = game.get("HomeTeamRuns")
    away_score = game.get("AwayTeamRuns")

    logger.info(f"Game status: {status}, {away_team} ({away_score}) at {home_team} ({home_score})")

    if status == "Final":
        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team

        if winner == "PIT":
            return RESOLUTION_MAP["Pittsburgh Pirates"]
        elif winner == "LAA":
            return RESOLUTION_MAP["Los Angeles Angels"]
    elif status in ["Canceled", "Postponed"]:
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    # Game date
    date = "2025-04-22"

    # Fetch game data
    game = fetch_game_data(date)

    # Determine resolution
    resolution = determine_resolution(game)

    # Output the recommendation
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()