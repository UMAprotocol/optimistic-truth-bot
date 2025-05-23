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
    "KCR": "p2",  # Kansas City Royals win maps to p2
    "DET": "p1",  # Detroit Tigers win maps to p1
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
    logger.info(f"Fetching game data for {date}")
    
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"
    logger.debug(f"Using API endpoint: {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        logger.info(f"Retrieved {len(games)} games for {date}")

        # Find the specific game between Kansas City Royals and Detroit Tigers
        for game in games:
            if (game['HomeTeam'] == "KCR" and game['AwayTeam'] == "DET") or (game['HomeTeam'] == "DET" and game['AwayTeam'] == "KCR"):
                logger.info(f"Found game: {game['AwayTeam']} at {game['HomeTeam']}")
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

    logger.info(f"Game status: {status}, {away_team} {away_score} - {home_team} {home_score}")

    if status == "Final":
        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team

        if winner == "KCR":
            return RESOLUTION_MAP["KCR"]
        elif winner == "DET":
            return RESOLUTION_MAP["DET"]
    elif status in ["Canceled", "Postponed"]:
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    date = "2025-04-20"
    game = fetch_game_data(date)
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()