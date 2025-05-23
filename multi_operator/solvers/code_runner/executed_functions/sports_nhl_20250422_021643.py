import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
RESOLUTION_MAP = {
    "DET": "p2",  # Detroit Pistons
    "NYK": "p1",  # New York Knicks
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

def fetch_nba_game_data():
    """
    Fetches NBA game data for the Pistons vs. Knicks game on the specified date.
    """
    date = "2025-04-21"
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}?key={NBA_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] == "DET" and game['AwayTeam'] == "NYK" or game['HomeTeam'] == "NYK" and game['AwayTeam'] == "DET":
                logger.info(f"Game found: {game['GameId']}")
                return game
        logger.warning("No matching game found.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch NBA game data: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return "p4"  # Too early to resolve

    if game['Status'] == "Final":
        if game['HomeTeam'] == "DET" and game['HomeTeamScore'] > game['AwayTeamScore']:
            return RESOLUTION_MAP["DET"]
        elif game['AwayTeam'] == "NYK" and game['AwayTeamScore'] > game['HomeTeamScore']:
            return RESOLUTION_MAP["NYK"]
        else:
            return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Postponed":
        return "p4"  # Market remains open
    else:
        return "p4"  # Too early to resolve

def main():
    """
    Main function to determine the resolution of the Pistons vs. Knicks game.
    """
    game_data = fetch_nba_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()