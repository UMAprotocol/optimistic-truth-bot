import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Check if API key is available
if not API_KEY:
    raise ValueError(
        "SPORTS_DATA_IO_NBA_API_KEY not found in environment variables. "
        "Please add it to your .env file."
    )

# Constants - RESOLUTION MAPPING using internal abbreviations
RESOLUTION_MAP = {
    "DAL": "p2",  # Dallas Mavericks maps to p2
    "MEM": "p1",  # Memphis Grizzlies maps to p1
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

def fetch_game_data():
    """
    Fetches game data for the specified NBA game between Dallas Mavericks and Memphis Grizzlies.

    Returns:
        Game data dictionary or None if not found
    """
    date = "2025-04-18"
    logger.info(f"Fetching game data for Mavericks vs Grizzlies on {date}")

    # Use the exact format from the API documentation with key as query parameter
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}?key={API_KEY}"
    
    try:
        logger.debug("Sending API request")
        response = requests.get(url, timeout=10)

        if response.status_code == 404:
            logger.warning(
                f"No data found for {date}. Please check the date and ensure data is available."
            )
            return None

        response.raise_for_status()
        games = response.json()
        logger.info(f"Retrieved {len(games)} games for {date}")

        # Find the specific game - the API returns an array of game objects
        for game_data in games:
            if game_data['HomeTeam'] == 'DAL' and game_data['AwayTeam'] == 'MEM':
                logger.info("Found the game: Mavericks vs Grizzlies")
                return game_data
            elif game_data['HomeTeam'] == 'MEM' and game_data['AwayTeam'] == 'DAL':
                logger.info("Found the game: Grizzlies vs Mavericks")
                return game_data

        logger.warning("No matching game found between Mavericks and Grizzlies on the specified date.")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.

    Args:
        game: Game data dictionary from the NBA API

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

    logger.info(
        f"Game status: {status}, Score: {away_team} {away_score} - {home_team} {home_score}"
    )

    if status == "Final":
        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team

        if winner == "DAL":
            return RESOLUTION_MAP["DAL"]
        elif winner == "MEM":
            return RESOLUTION_MAP["MEM"]
    elif status == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif status in ["Scheduled", "InProgress"]:
        return RESOLUTION_MAP["Too early to resolve"]

    return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to query NBA game data and determine the resolution.
    """
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()