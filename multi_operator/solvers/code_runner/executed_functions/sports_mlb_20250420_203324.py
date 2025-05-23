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
    "CLE": "p2",  # Cleveland Guardians maps to p2
    "PIT": "p1",  # Pittsburgh Pirates maps to p1
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
    date = datetime.now().strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == 'CLE' and game['AwayTeam'] == 'PIT':
                return game
            elif game['HomeTeam'] == 'PIT' and game['AwayTeam'] == 'CLE':
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
            winner = home_team
        else:
            winner = away_team

        return RESOLUTION_MAP.get(winner, "p3")
    elif status in ["Postponed", "Canceled"]:
        return "p3"
    else:
        return "p4"

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()