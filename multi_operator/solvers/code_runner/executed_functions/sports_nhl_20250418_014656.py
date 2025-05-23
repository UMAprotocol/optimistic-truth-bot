import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "TBL": "p2",  # Tampa Bay Lightning
    "NYR": "p1",  # New York Rangers
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
            if game['HomeTeam'] == 'TBL' and game['AwayTeam'] == 'NYR' or game['HomeTeam'] == 'NYR' and game['AwayTeam'] == 'TBL':
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
        return "recommendation: p4"

    if game['Status'] == "Canceled":
        return "recommendation: p3"
    elif game['Status'] == "Final":
        if game['HomeTeam'] == 'TBL' and game['HomeTeamScore'] > game['AwayTeamScore']:
            return "recommendation: p2"
        elif game['AwayTeam'] == 'NYR' and game['AwayTeamScore'] > game['HomeTeamScore']:
            return "recommendation: p1"
        else:
            return "recommendation: p3"
    else:
        return "recommendation: p4"

def main():
    game_data = fetch_nhl_game_data()
    resolution = determine_resolution(game_data)
    print(resolution)

if __name__ == "__main__":
    main()