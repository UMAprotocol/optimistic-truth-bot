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
    "Cubs": "p2",  # Chicago Cubs win maps to p2
    "Padres": "p1",  # San Diego Padres win maps to p1
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
    Fetches game data for the Chicago Cubs vs. San Diego Padres game scheduled for April 14, 2025.

    Returns:
        Game data dictionary or None if not found
    """
    date = "2025-04-14"
    team1_name = "Chicago Cubs"
    team2_name = "San Diego Padres"
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == "SD" and game['AwayTeam'] == "CHC":
                return game
            elif game['HomeTeam'] == "CHC" and game['AwayTeam'] == "SD":
                return game

        logger.info("No matching game found for the specified date and teams.")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.

    Args:
        game: Game data dictionary from the API

    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    if not game:
        return "p4"  # Too early to resolve

    status = game.get("Status")
    if status == "Final":
        home_team = game.get("HomeTeam")
        away_team = game.get("AwayTeam")
        home_score = game.get("HomeTeamRuns")
        away_score = game.get("AwayTeamRuns")

        if home_score > away_score:
            winner = "Padres" if home_team == "SD" else "Cubs"
        else:
            winner = "Padres" if away_team == "SD" else "Cubs"

        return RESOLUTION_MAP[winner]
    elif status in ["Canceled", "Postponed"]:
        return "p3"  # Game canceled or postponed, resolve as 50-50
    else:
        return "p4"  # Game not completed or no valid status

def main():
    """
    Main function to determine the resolution of the Chicago Cubs vs. San Diego Padres game.
    """
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()