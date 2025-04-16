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

# Constants - RESOLUTION MAPPING using team names
RESOLUTION_MAP = {
    "Guardians": "p2",  # Cleveland Guardians win maps to p2
    "Orioles": "p1",    # Baltimore Orioles win maps to p1
    "50-50": "p3",      # Tie or undetermined maps to p3
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
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        # Find the specific game between Cleveland Guardians and Baltimore Orioles
        for game in games:
            if (game['HomeTeam'] == "CLE" and game['AwayTeam'] == "BAL") or (game['HomeTeam'] == "BAL" and game['AwayTeam'] == "CLE"):
                return game
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
        home_team = game.get("HomeTeam")
        away_team = game.get("AwayTeam")
        home_score = game.get("HomeTeamRuns")
        away_score = game.get("AwayTeamRuns")

        if home_score > away_score:
            winner = "Guardians" if home_team == "CLE" else "Orioles"
        else:
            winner = "Orioles" if away_team == "BAL" else "Guardians"

        return RESOLUTION_MAP[winner]
    elif status in ["Canceled", "Postponed"]:
        return "p3"  # Game canceled or postponed, resolve as 50-50
    else:
        return "p4"  # Game not final, too early to resolve

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    # Game date
    date = "2025-04-15"

    # Fetch game data
    game = fetch_game_data(date)

    # Determine resolution
    resolution = determine_resolution(game)

    # Output the recommendation
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()