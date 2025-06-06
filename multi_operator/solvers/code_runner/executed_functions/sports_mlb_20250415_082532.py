import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
print(API_KEY)

# Check if API key is available
if not API_KEY:
    raise ValueError(
        "SPORTS_DATA_IO_MLB_API_KEY not found in environment variables. "
        "Please add it to your .env file."
    )

# Constants - RESOLUTION MAPPING using team names
RESOLUTION_MAP = {
    "DET": "p2",  # Detroit Tigers win maps to p2
    "MIL": "p1",  # Milwaukee Brewers win maps to p1
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
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDateFinal/{date}?key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        # Find the specific game between Detroit Tigers and Milwaukee Brewers
        for game in games:
            if (game['HomeTeam'] == "DET" and game['AwayTeam'] == "MIL") or (game['HomeTeam'] == "MIL" and game['AwayTeam'] == "DET"):
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
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

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

        return "recommendation: " + RESOLUTION_MAP[winner]
    elif status == "Canceled":
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    elif status == "Postponed":
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    else:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    # Game date for Detroit Tigers vs. Milwaukee Brewers on April 14, 2025
    date = "2025-04-14"

    # Fetch game data
    game = fetch_game_data(date)
    
    # Determine resolution
    resolution = determine_resolution(game)
    
    # Output the recommendation
    print(resolution)

if __name__ == "__main__":
    main()