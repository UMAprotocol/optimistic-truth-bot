import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants - RESOLUTION MAPPING using internal abbreviations
RESOLUTION_MAP = {
    "MIA": "p2",  # Miami Heat maps to p2
    "CHI": "p1",  # Chicago Bulls maps to p1
    "50-50": "p3",  # Canceled or unresolved maps to p3
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def fetch_game_data(date, team1_abbr, team2_abbr):
    """
    Fetches game data for the specified date and teams.

    Args:
        date: Game date in YYYY-MM-DD format
        team1_abbr: Abbreviation of the first team
        team2_abbr: Abbreviation of the second team

    Returns:
        Game data dictionary or None if not found
    """
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}?key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if (game['HomeTeam'] == team1_abbr and game['AwayTeam'] == team2_abbr) or \
               (game['HomeTeam'] == team2_abbr and game['AwayTeam'] == team1_abbr):
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
        Resolution string (p1, p2, p3)
    """
    if not game:
        return "p3"  # Assume 50-50 if no game data is available

    if game['Status'] == "Final":
        if game['HomeTeamScore'] > game['AwayTeamScore']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']

        return RESOLUTION_MAP.get(winner, "p3")
    elif game['Status'] in ["Canceled", "Postponed"]:
        return "p3"
    else:
        return "p3"  # Default to 50-50 for any other unhandled statuses

def main():
    """
    Main function to query NBA game data and determine the resolution.
    """
    date = "2025-04-16"
    team1_abbr = "MIA"
    team2_abbr = "CHI"

    game = fetch_game_data(date, team1_abbr, team2_abbr)
    resolution = determine_resolution(game)
    
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()