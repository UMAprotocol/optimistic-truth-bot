import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Check if API key is available
if not API_KEY:
    raise ValueError(
        "SPORTS_DATA_IO_NHL_API_KEY not found in environment variables. "
        "Please add it to your .env file."
    )

# Constants - RESOLUTION MAPPING using internal abbreviations
RESOLUTION_MAP = {
    "ATL": "p2",  # Atlanta Hawks maps to p2
    "ORL": "p1",  # Orlando Magic maps to p1
    "50-50": "p3",  # Tie or undetermined maps to p3
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
    logger.info(f"Fetching game data for NBA games on {date}")

    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}?key={API_KEY}"
    logger.debug(f"Using API endpoint: {url}")

    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()
        logger.info(f"Retrieved {len(games)} games for {date}")

        # Find the specific game - the API returns an array of game objects
        for game in games:
            if game['HomeTeam'] == 'ATL' and game['AwayTeam'] == 'ORL' or game['HomeTeam'] == 'ORL' and game['AwayTeam'] == 'ATL':
                logger.info(f"Found matching game: {game['AwayTeam']} @ {game['HomeTeam']}")
                return game

        logger.warning("No matching game found for Atlanta Hawks vs Orlando Magic on the specified date.")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.

    Args:
        game: Game data dictionary from the API

    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    if not game:
        logger.info("No game data available, returning 'Too early to resolve'")
        return RESOLUTION_MAP["Too early to resolve"]

    status = game.get("Status")
    home_team = game.get("HomeTeam")
    away_team = game.get("AwayTeam")
    home_score = game.get("HomeTeamScore")
    away_score = game.get("AwayTeamScore")

    logger.info(f"Game status: {status}, Score: {away_team} {away_score} - {home_team} {home_score}")

    if status == "Final":
        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team

        if winner == "ATL":
            return RESOLUTION_MAP["ATL"]
        elif winner == "ORL":
            return RESOLUTION_MAP["ORL"]
    elif status == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif status == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]

    return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to query NBA game data and determine the resolution.
    """
    date = "2025-04-15"
    game = fetch_game_data(date)
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()