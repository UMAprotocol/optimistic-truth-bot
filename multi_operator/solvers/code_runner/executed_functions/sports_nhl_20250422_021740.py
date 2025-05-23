import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants for resolution mapping
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
                logger.info("Game found: Pistons vs. Knicks")
                return game
        logger.warning("No game found for Pistons vs. Knicks on the specified date.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch NBA game data: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return "recommendation: p4"  # Too early to resolve or no data

    if game['Status'] == "Final":
        if game['HomeTeam'] == "DET" and game['HomeTeamScore'] > game['AwayTeamScore']:
            return "recommendation: p2"  # Pistons win
        elif game['AwayTeam'] == "NYK" and game['AwayTeamScore'] > game['HomeTeamScore']:
            return "recommendation: p1"  # Knicks win
    elif game['Status'] == "Canceled":
        return "recommendation: p3"  # 50-50
    elif game['Status'] == "Postponed":
        return "recommendation: p4"  # Too early to resolve

    return "recommendation: p4"  # Default case if none of the above conditions are met

def main():
    """
    Main function to fetch NBA game data and determine the resolution.
    """
    game_data = fetch_nba_game_data()
    resolution = determine_resolution(game_data)
    print(resolution)

if __name__ == "__main__":
    main()