import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants - RESOLUTION MAPPING using internal abbreviations
RESOLUTION_MAP = {
    "WAS": "p2",  # Washington Nationals win maps to p2
    "COL": "p1",  # Colorado Rockies win maps to p1
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
    date = "2025-04-20"
    team1_api = "WAS"
    team2_api = "COL"
    
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game["HomeTeam"] == team1_api and game["AwayTeam"] == team2_api:
                return game
            elif game["HomeTeam"] == team2_api and game["AwayTeam"] == team1_api:
                return game

        logger.info("No matching game found.")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return "p4"  # No game data available

    status = game.get("Status")
    if status == "Final":
        home_team = game["HomeTeam"]
        away_team = game["AwayTeam"]
        home_score = game["HomeTeamRuns"]
        away_score = game["AwayTeamRuns"]

        if home_score > away_score:
            return RESOLUTION_MAP.get(home_team, "p3")
        elif away_score > home_score:
            return RESOLUTION_MAP.get(away_team, "p3")
        else:
            return "p3"  # Tie case
    elif status in ["Canceled", "Postponed"]:
        return "p3"  # Game not played or postponed
    else:
        return "p4"  # Game not completed yet

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()