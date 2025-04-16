import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants - RESOLUTION MAPPING using team names
RESOLUTION_MAP = {
    "Washington Nationals": "p2",  # Washington Nationals win maps to p2
    "Pittsburgh Pirates": "p1",    # Pittsburgh Pirates win maps to p1
    "50-50": "p3",                 # Tie or undetermined maps to p3
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
        return games
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch game data: {e}")
        return None

def determine_resolution(games):
    """
    Determines the resolution based on the game's status and outcome.

    Args:
        games: List of games data from the API

    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    for game in games:
        if game['HomeTeam'] == "WAS" and game['AwayTeam'] == "PIT":
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return "recommendation: " + RESOLUTION_MAP["Washington Nationals"]
                elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                    return "recommendation: " + RESOLUTION_MAP["Pittsburgh Pirates"]
            elif game['Status'] in ["Postponed", "Canceled"]:
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            else:
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    date = "2025-04-15"
    games = fetch_game_data(date)
    if games:
        resolution = determine_resolution(games)
    else:
        resolution = "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    print(resolution)

if __name__ == "__main__":
    main()