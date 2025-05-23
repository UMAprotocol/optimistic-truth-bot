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
    "Athletics": "p2",  # Athletics win maps to p2
    "Milwaukee Brewers": "p1",  # Milwaukee Brewers win maps to p1
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
        games: List of game data dictionaries

    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    for game in games:
        if game['AwayTeam'] == "OAK" and game['HomeTeam'] == "MIL":
            if game['Status'] == "Final":
                if game['AwayTeamRuns'] > game['HomeTeamRuns']:
                    return "recommendation: " + RESOLUTION_MAP["Athletics"]
                elif game['AwayTeamRuns'] < game['HomeTeamRuns']:
                    return "recommendation: " + RESOLUTION_MAP["Milwaukee Brewers"]
            elif game['Status'] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            elif game['Status'] == "Postponed":
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    date = "2025-04-19"
    games = fetch_game_data(date)
    if games is None:
        print("recommendation: p4")
    else:
        resolution = determine_resolution(games)
        print(resolution)

if __name__ == "__main__":
    main()