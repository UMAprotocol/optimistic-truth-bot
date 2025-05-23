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
    "PHI": "p2",  # Philadelphia Phillies win maps to p2
    "NYM": "p1",  # New York Mets win maps to p1
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
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"
    logger.debug(f"Fetching game data for {date} using URL: {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        # Find the game between Philadelphia Phillies and New York Mets
        for game in games:
            if (game['HomeTeam'] == "PHI" and game['AwayTeam'] == "NYM") or (game['HomeTeam'] == "NYM" and game['AwayTeam'] == "PHI"):
                logger.info(f"Found the game: {game}")
                return game
        logger.warning("No game found between Philadelphia Phillies and New York Mets on this date.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch game data: {e}")
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
        return "p4"  # Too early to resolve

    status = game.get("Status")
    if status == "Final":
        home_team = game['HomeTeam']
        away_team = game['AwayTeam']
        home_score = game['HomeTeamRuns']
        away_score = game['AwayTeamRuns']

        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team

        return RESOLUTION_MAP.get(winner, "p3")
    elif status in ["Postponed", "Canceled"]:
        return "p3"  # Resolve as 50-50 if game is postponed or canceled
    else:
        return "p4"  # Too early to resolve

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    # Date of the game
    game_date = "2025-04-23"

    # Fetch game data
    game = fetch_game_data(game_date)
    
    # Determine resolution
    resolution = determine_resolution(game)
    
    # Output the recommendation
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()