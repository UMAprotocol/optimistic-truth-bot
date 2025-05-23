import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
RESOLUTION_MAP = {
    "MIA": "p2",  # Miami Heat
    "CLE": "p1",  # Cleveland Cavaliers
    "50-50": "p3",
    "Too early to resolve": "p4",
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
    Fetches game data for the Miami Heat vs. Cleveland Cavaliers game scheduled on 2025-04-20.
    """
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/2025-04-20?key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == 'MIA' and game['AwayTeam'] == 'CLE' or game['HomeTeam'] == 'CLE' and game['AwayTeam'] == 'MIA':
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
        return RESOLUTION_MAP["Too early to resolve"]

    if game['Status'] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]
    elif game['Status'] == "Final":
        if game['HomeTeam'] == 'MIA' and game['HomeTeamScore'] > game['AwayTeamScore']:
            return RESOLUTION_MAP["MIA"]
        elif game['AwayTeam'] == 'MIA' and game['AwayTeamScore'] > game['HomeTeamScore']:
            return RESOLUTION_MAP["MIA"]
        else:
            return RESOLUTION_MAP["CLE"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to determine the resolution of the NBA game between Miami Heat and Cleveland Cavaliers.
    """
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()