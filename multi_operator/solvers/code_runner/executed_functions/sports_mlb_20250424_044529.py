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
    "Texas Rangers": "p2",  # Texas Rangers win maps to p2
    "Athletics": "p1",      # Athletics win maps to p1
    "50-50": "p3",          # Tie or undetermined maps to p3
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
    date = "2025-04-23"
    team1_name = "Texas Rangers"
    team2_name = "Athletics"
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if (game['HomeTeam'] == team1_name and game['AwayTeam'] == team2_name) or \
               (game['HomeTeam'] == team2_name and game['AwayTeam'] == team1_name):
                return game
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
        home_team = game.get("HomeTeam")
        away_team = game.get("AwayTeam")
        home_score = game.get("HomeTeamRuns")
        away_score = game.get("AwayTeamRuns")

        if home_score > away_score:
            return RESOLUTION_MAP.get(home_team, "p3")
        elif away_score > home_score:
            return RESOLUTION_MAP.get(away_team, "p3")
        else:
            return "p3"  # Tie case
    elif status == "Canceled":
        return "p3"  # Game canceled, resolve as 50-50
    elif status == "Postponed":
        return "p4"  # Game postponed, too early to resolve

    return "p4"  # Default case if none of the above conditions are met

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()