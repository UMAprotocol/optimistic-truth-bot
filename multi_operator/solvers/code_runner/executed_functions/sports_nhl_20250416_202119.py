import os
import requests
from dotenv import load_dotenv
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants - RESOLUTION MAPPING using NHL team abbreviations
RESOLUTION_MAP = {
    "CHI": "p2",  # Chicago Blackhawks
    "OTT": "p1",  # Ottawa Senators
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

def fetch_game_data(date, team1_abbr, team2_abbr):
    """
    Fetches game data for the specified date and teams.

    Args:
        date: Game date in YYYY-MM-DD format
        team1_abbr: Abbreviation for first team
        team2_abbr: Abbreviation for second team

    Returns:
        Game data dictionary or None if not found
    """
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}?key={API_KEY}"
    try:
        response = requests.get(url)
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
        Resolution string (p1, p2, p3, or p4)
    """
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]

    if game['Status'] == "Final":
        if game['HomeTeamScore'] > game['AwayTeamScore']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']

        if winner == "CHI":
            return RESOLUTION_MAP["CHI"]
        elif winner == "OTT":
            return RESOLUTION_MAP["OTT"]
    elif game['Status'] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]

    return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to query NHL game data and determine the resolution.
    """
    date = "2025-04-15"
    team1_abbr = "CHI"
    team2_abbr = "OTT"

    game = fetch_game_data(date, team1_abbr, team2_abbr)
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()