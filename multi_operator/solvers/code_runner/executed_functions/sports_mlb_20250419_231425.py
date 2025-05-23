import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants - RESOLUTION MAPPING using internal abbreviations
RESOLUTION_MAP = {
    "Chicago White Sox": "p2",  # Chicago White Sox win maps to p2
    "Boston Red Sox": "p1",    # Boston Red Sox win maps to p1
    "50-50": "p3",             # Canceled or no make-up game maps to p3
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
    logger.info(f"Fetching game data for MLB games on {date}")
    
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"
    logger.debug(f"Using API endpoint: {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        logger.info(f"Retrieved {len(games)} games for {date}")

        # Find the specific game between Chicago White Sox and Boston Red Sox
        for game in games:
            if (game['HomeTeam'] == "CWS" and game['AwayTeam'] == "BOS") or (game['HomeTeam'] == "BOS" and game['AwayTeam'] == "CWS"):
                logger.info(f"Found game: {game['AwayTeam']} at {game['HomeTeam']}")
                return game

        logger.warning("No matching game found between Chicago White Sox and Boston Red Sox on the specified date.")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.

    Args:
        game: Game data dictionary from the GamesByDate endpoint

    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    if not game:
        logger.info("No game data available, returning 'Too early to resolve'")
        return RESOLUTION_MAP["Too early to resolve"]

    status = game.get("Status")
    logger.info(f"Game status: {status}")

    if status == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']

        if winner == "CWS":
            return RESOLUTION_MAP["Chicago White Sox"]
        elif winner == "BOS":
            return RESOLUTION_MAP["Boston Red Sox"]
    elif status in ["Postponed", "Canceled"]:
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    # Game date for the Chicago White Sox vs. Boston Red Sox
    date = "2025-04-19"
    
    # Fetch game data
    game = fetch_game_data(date)
    
    # Determine resolution
    resolution = determine_resolution(game)
    
    # Output the recommendation
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()