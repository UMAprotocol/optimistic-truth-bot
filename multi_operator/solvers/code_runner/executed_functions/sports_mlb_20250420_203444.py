import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants - RESOLUTION MAPPING using internal abbreviations
RESOLUTION_MAP = {
    "Kansas City Royals": "p2",  # Kansas City Royals win maps to p2
    "Detroit Tigers": "p1",      # Detroit Tigers win maps to p1
    "50-50": "p3",               # Tie or undetermined maps to p3
    "Too early to resolve": "p4" # Incomplete data maps to p4
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
            if game['HomeTeam'] == 'KC' and game['AwayTeam'] == 'DET' or game['HomeTeam'] == 'DET' and game['AwayTeam'] == 'KC':
                logger.info(f"Found game: {game['HomeTeam']} vs {game['AwayTeam']}")
                return game
        logger.warning("No game found for Kansas City Royals vs Detroit Tigers on the specified date.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch game data: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return "recommendation: p4"

    if game['Status'] == 'Final':
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']

        if winner == 'KC':
            return "recommendation: p2"
        elif winner == 'DET':
            return "recommendation: p1"
    elif game['Status'] == 'Canceled':
        return "recommendation: p3"
    elif game['Status'] == 'Postponed':
        return "recommendation: p4"

    return "recommendation: p4"

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(resolution)

if __name__ == "__main__":
    main()