import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "TBL": "p2",  # Tampa Bay Lightning
    "NYR": "p1",  # New York Rangers
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_nhl_game_data():
    """
    Fetches NHL game data for the specified game.
    """
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-17?key={NHL_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] == 'TBL' and game['AwayTeam'] == 'NYR':
                return game
            elif game['HomeTeam'] == 'NYR' and game['AwayTeam'] == 'TBL':
                return game
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch NHL game data: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]

    if game['Status'] == "Final":
        if game['HomeTeamScore'] > game['AwayTeamScore']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        
        if winner == "TBL":
            return RESOLUTION_MAP["TBL"]
        elif winner == "NYR":
            return RESOLUTION_MAP["NYR"]
    elif game['Status'] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]

    return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to determine the resolution of the NHL game.
    """
    game_data = fetch_nhl_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()