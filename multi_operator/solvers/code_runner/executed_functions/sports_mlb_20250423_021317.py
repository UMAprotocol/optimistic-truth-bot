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
    logger.info(f"Fetching game data for {date} using URL: {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        # Find the specific game between Philadelphia Phillies and New York Mets
        for game in games:
            if (game['HomeTeam'] == "PHI" and game['AwayTeam'] == "NYM") or (game['HomeTeam'] == "NYM" and game['AwayTeam'] == "PHI"):
                logger.info(f"Found game between PHI and NYM on {date}")
                return game
        logger.warning("No game found between PHI and NYM on the specified date.")
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
        logger.info("No game data available, returning 'Too early to resolve'")
        return "recommendation: p4"

    status = game.get("Status")
    if status == "Final":
        home_team = game.get("HomeTeam")
        away_team = game.get("AwayTeam")
        home_score = game.get("HomeTeamRuns")
        away_score = game.get("AwayTeamRuns")

        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team

        resolution = RESOLUTION_MAP.get(winner, "p3")
        logger.info(f"Game finished. Winner: {winner}. Resolution: {resolution}")
        return f"recommendation: {resolution}"
    elif status in ["Postponed", "Canceled"]:
        logger.info(f"Game was {status}. Resolving as 50-50.")
        return "recommendation: p3"
    else:
        logger.info(f"Game status is {status}. Too early to resolve.")
        return "recommendation: p4"

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    # The date of the game in question
    game_date = "2025-04-22"

    # Fetch game data
    game = fetch_game_data(game_date)
    
    # Determine resolution
    resolution = determine_resolution(game)
    
    # Output the recommendation
    print(resolution)

if __name__ == "__main__":
    main()