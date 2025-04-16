import os
import requests
from dotenv import load_dotenv
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

# Constants - RESOLUTION MAPPING using internal abbreviations
RESOLUTION_MAP = {
    "Punjab Kings": "p2",
    "Kolkata Knight Riders": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4",
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
    Fetches game data for the specified IPL game.

    Returns:
        Game data dictionary or None if not found
    """
    date = "2025-04-15"
    team1_name = "Punjab Kings"
    team2_name = "Kolkata Knight Riders"
    url = f"https://api.sportsdata.io/v3/cricket/scores/json/GamesByDate/{date}?key={API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeamName'] == team1_name and game['AwayTeamName'] == team2_name:
                return game
            elif game['HomeTeamName'] == team2_name and game['AwayTeamName'] == team1_name:
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
        return "p4"

    status = game.get("Status")
    home_team = game.get("HomeTeamName")
    away_team = game.get("AwayTeamName")
    home_score = game.get("HomeTeamScore")
    away_score = game.get("AwayTeamScore")

    if status == "Postponed":
        return "p4"
    elif status == "Canceled":
        return "p3"
    elif status == "Completed":
        if home_score > away_score:
            return RESOLUTION_MAP[home_team]
        elif away_score > home_score:
            return RESOLUTION_MAP[away_team]
        else:
            return "p3"
    else:
        return "p4"

def main():
    """
    Main function to query IPL game data and determine the resolution.
    """
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()