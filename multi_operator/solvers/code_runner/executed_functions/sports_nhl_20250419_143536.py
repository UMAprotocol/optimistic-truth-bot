import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "GT": "p2",  # Gujarat Titans
    "DC": "p1",  # Delhi Capitals
    "50-50": "p3",
    "Too early to resolve": "p4",
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
    Fetches game data for the specified IPL game.
    
    Returns:
        Game data dictionary or None if not found
    """
    date = "2025-04-19"
    team1 = "GT"
    team2 = "DC"
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}?key={API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
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
        home_team = game.get("HomeTeam")
        away_team = game.get("AwayTeam")
        home_score = game.get("HomeTeamScore")
        away_score = game.get("AwayTeamScore")

        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team

        if winner == "GT":
            return RESOLUTION_MAP["GT"]
        elif winner == "DC":
            return RESOLUTION_MAP["DC"]
    elif status == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif status == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]

    return RESOLUTION_MAP["Too early to resolve"]

def main():
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()