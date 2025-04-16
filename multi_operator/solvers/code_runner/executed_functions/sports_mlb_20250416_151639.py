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
    "LAA": "p2",  # Los Angeles Angels win maps to p2
    "TEX": "p1",  # Texas Rangers win maps to p1
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

def fetch_game_data(date, team1_api, team2_api):
    """
    Fetches game data for the specified date and teams.
    """
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if (game['HomeTeam'] == team1_api and game['AwayTeam'] == team2_api) or (game['HomeTeam'] == team2_api and game['AwayTeam'] == team1_api):
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
        return "p4"

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
            return "p3"
    elif status in ["Canceled", "Postponed"]:
        return "p3"
    else:
        return "p4"

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    date = "2025-04-15"
    team1_api = "LAA"  # Los Angeles Angels
    team2_api = "TEX"  # Texas Rangers

    game = fetch_game_data(date, team1_api, team2_api)
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()