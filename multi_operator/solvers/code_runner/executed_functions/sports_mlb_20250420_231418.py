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
    "ARI": "p2",  # Arizona Diamondbacks maps to p2
    "CHC": "p1",  # Chicago Cubs maps to p1
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
    team1_name = "Arizona Diamondbacks"
    team2_name = "Chicago Cubs"
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == 'CHC' and game['AwayTeam'] == 'ARI':
                return game
            elif game['HomeTeam'] == 'ARI' and game['AwayTeam'] == 'CHC':
                return game

        logger.info("No game found for the specified teams on the specified date.")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return "recommendation: p4"

    status = game['Status']
    if status == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']

        if winner == "CHC":
            return "recommendation: p1"
        elif winner == "ARI":
            return "recommendation: p2"
    elif status in ["Canceled", "Postponed"]:
        return "recommendation: p3"
    else:
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