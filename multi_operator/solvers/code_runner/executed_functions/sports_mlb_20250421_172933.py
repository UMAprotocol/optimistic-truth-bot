import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants - RESOLUTION MAPPING using team names
RESOLUTION_MAP = {
    "Chicago White Sox": "p2",  # Chicago White Sox win maps to p2
    "Boston Red Sox": "p1",    # Boston Red Sox win maps to p1
    "50-50": "p3",             # Tie or undetermined maps to p3
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

def fetch_game_data():
    """
    Fetches game data for the specified date and teams.
    """
    date = datetime.now().strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"
    logger.info(f"Fetching game data for {date} from {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == 'CHW' and game['AwayTeam'] == 'BOS' or game['HomeTeam'] == 'BOS' and game['AwayTeam'] == 'CHW':
                logger.info(f"Found game: {game['GameID']}")
                return game
        logger.warning("No matching game found.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch game data: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return "p4"  # No game data available

    if game['Status'] == 'Final':
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']

        if winner == 'CHW':
            return RESOLUTION_MAP["Chicago White Sox"]
        elif winner == 'BOS':
            return RESOLUTION_MAP["Boston Red Sox"]
    elif game['Status'] in ['Canceled', 'Postponed']:
        return "p3"  # Game not played or postponed

    return "p4"  # Game not final or data insufficient

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()