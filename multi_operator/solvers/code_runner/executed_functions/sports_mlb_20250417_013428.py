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
    "Kansas City Royals": "p2",  # Kansas City Royals win maps to p2
    "New York Yankees": "p1",   # New York Yankees win maps to p1
    "50-50": "p3",              # Tie or undetermined maps to p3
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
    logger.info(f"Fetching game data for date: {date}")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        logger.info(f"Retrieved {len(games)} games for {date}")
        return games
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
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
        if "Kansas City Royals" in [game["HomeTeam"], game["AwayTeam"]] and "New York Yankees" in [game["HomeTeam"], game["AwayTeam"]]:
            if game["Status"] == "Final":
                home_team = game["HomeTeam"]
                away_team = game["AwayTeam"]
                home_score = game["HomeTeamRuns"]
                away_score = game["AwayTeamRuns"]
                if home_score > away_score:
                    winner = home_team
                else:
                    winner = away_team
                return f"recommendation: {RESOLUTION_MAP.get(winner, 'p3')}"
            elif game["Status"] in ["Postponed", "Canceled"]:
                return "recommendation: p3"
            else:
                return "recommendation: p4"
    return "recommendation: p4"

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    date = "2025-04-16"
    games = fetch_game_data(date)
    if games is None:
        print("recommendation: p4")
    else:
        resolution = determine_resolution(games)
        print(resolution)

if __name__ == "__main__":
    main()