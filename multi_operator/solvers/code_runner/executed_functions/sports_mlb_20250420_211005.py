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
    "LAD": "p2",  # Los Angeles Dodgers win maps to p2
    "TEX": "p1",  # Texas Rangers win maps to p1
    "50-50": "p3",  # Tie or undetermined maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_game_data():
    """
    Fetches game data for the specified date and teams.
    """
    date = "2025-04-20"
    team1_api = "LAD"
    team2_api = "TEX"
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == team1_api and game['AwayTeam'] == team2_api:
                return game
            elif game['HomeTeam'] == team2_api and game['AwayTeam'] == team1_api:
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
        return "p4"  # Too early to resolve

    status = game.get("Status")
    if status in ["Scheduled", "InProgress", "Delayed", "Suspended"]:
        return "p4"  # Too early to resolve
    elif status == "Final":
        home_score = game.get("HomeTeamRuns")
        away_score = game.get("AwayTeamRuns")
        if home_score > away_score:
            return RESOLUTION_MAP[game.get("HomeTeam")]
        else:
            return RESOLUTION_MAP[game.get("AwayTeam")]
    elif status in ["Postponed", "Canceled"]:
        return "p3"  # 50-50 resolution

    return "p4"  # Default to too early to resolve if none of the above

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()