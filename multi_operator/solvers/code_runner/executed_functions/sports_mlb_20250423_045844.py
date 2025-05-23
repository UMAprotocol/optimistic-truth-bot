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
    "TEX": "p2",  # Texas Rangers maps to p2
    "OAK": "p1",  # Athletics maps to p1
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

def fetch_game_data():
    """
    Fetches game data for the specified date and teams.
    """
    date = "2025-04-22"
    team1_name = "Texas Rangers"
    team2_name = "Athletics"
    
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"
    logger.info(f"Fetching game data for {team1_name} vs {team2_name} on {date}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == "TEX" and game['AwayTeam'] == "OAK" or game['HomeTeam'] == "OAK" and game['AwayTeam'] == "TEX":
                logger.info(f"Found game: {game['GameID']}")
                return game
        logger.warning("No matching game found.")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        logger.info("No game data available, returning 'Too early to resolve'")
        return "recommendation: p4"

    status = game.get("Status")
    home_team = game.get("HomeTeam")
    away_team = game.get("AwayTeam")
    home_score = game.get("HomeTeamRuns")
    away_score = game.get("AwayTeamRuns")

    if status == "Final":
        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team

        if winner == "TEX":
            return "recommendation: p2"
        elif winner == "OAK":
            return "recommendation: p1"
    elif status == "Canceled":
        return "recommendation: p3"
    elif status == "Postponed":
        return "recommendation: p4"

    return "recommendation: p4"

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(resolution)

if __name__ == "__main__":
    main()