import os
import requests
from dotenv import load_dotenv
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants - RESOLUTION MAPPING using team names
RESOLUTION_MAP = {
    "Boston Red Sox": "p2",  # Boston Red Sox win maps to p2
    "Tampa Bay Rays": "p1",  # Tampa Bay Rays win maps to p1
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

def fetch_game_data(date, team1_name, team2_name):
    """
    Fetches game data for the specified date and teams.

    Args:
        date: Game date in YYYY-MM-DD format
        team1_name: First team name
        team2_name: Second team name

    Returns:
        Game data dictionary or None if not found
    """
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"
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

    Args:
        game: Game data dictionary

    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    if not game:
        return "p4"  # Too early to resolve

    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']

        return RESOLUTION_MAP.get(winner, "p3")
    elif game['Status'] in ["Canceled", "Postponed"]:
        return "p3"  # 50-50 resolution
    else:
        return "p4"  # Too early to resolve

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    date = "2025-04-16"
    team1_name = "Boston Red Sox"
    team2_name = "Tampa Bay Rays"

    game = fetch_game_data(date, team1_name, team2_name)
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()