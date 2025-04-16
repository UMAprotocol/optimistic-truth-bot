import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Check if API key is available
if not API_KEY:
    raise ValueError(
        "SPORTS_DATA_IO_MLB_API_KEY not found in environment variables. "
        "Please add it to your .env file."
    )

# Constants - RESOLUTION MAPPING using team names
RESOLUTION_MAP = {
    "Diamondbacks": "p2",  # Arizona Diamondbacks win maps to p2
    "Marlins": "p1",       # Miami Marlins win maps to p1
    "50-50": "p3",         # Tie or undetermined maps to p3
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

def fetch_game_data(date, team1_name, team2_name):
    """
    Fetches game data for the specified date and teams.

    Args:
        date: Game date in YYYY-MM-DD format
        team1_name: First team name (full name)
        team2_name: Second team name (full name)

    Returns:
        Game data dictionary or None if not found
    """
    logger.info(f"Fetching game data for game between {team1_name} and {team2_name} on {date}")

    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if (game['HomeTeam'] == team1_name or game['AwayTeam'] == team1_name) and \
               (game['HomeTeam'] == team2_name or game['AwayTeam'] == team2_name):
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
        return "p4"

    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']

        if winner == "ARI":
            return "p2"
        elif winner == "MIA":
            return "p1"
    elif game['Status'] == "Canceled":
        return "p3"
    elif game['Status'] == "Postponed":
        return "p4"

    return "p4"

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    date = "2025-04-15"
    team1_name = "ARI"
    team2_name = "MIA"

    game = fetch_game_data(date, team1_name, team2_name)
    resolution = determine_resolution(game)

    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()