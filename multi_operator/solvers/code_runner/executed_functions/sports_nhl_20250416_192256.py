import os
import requests
from dotenv import load_dotenv
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants - RESOLUTION MAPPING using team abbreviations
RESOLUTION_MAP = {
    "MEM": "p2",  # Memphis Grizzlies maps to p2
    "GSW": "p1",  # Golden State Warriors maps to p1
    "50-50": "p3",  # Canceled or unresolved maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_game_data():
    """
    Fetches game data for the specified NBA game between Memphis Grizzlies and Golden State Warriors.

    Returns:
        Game data dictionary or None if not found
    """
    date = "2025-04-15"
    team1 = "MEM"
    team2 = "GSW"
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}?key={API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == team1 and game['AwayTeam'] == team2 or game['HomeTeam'] == team2 and game['AwayTeam'] == team1:
                return game
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
        return RESOLUTION_MAP["Too early to resolve"]

    status = game.get("Status")
    if status == "Final":
        home_team = game['HomeTeam']
        away_team = game['AwayTeam']
        home_score = game['HomeTeamScore']
        away_score = game['AwayTeamScore']

        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team

        return RESOLUTION_MAP.get(winner, "p3")
    elif status == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif status == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to query NBA game data and determine the resolution.
    """
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()