import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "LAC": "p2",  # LA Clippers
    "DEN": "p1",  # Denver Nuggets
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

def fetch_nba_game_data():
    """
    Fetches NBA game data for the Clippers vs. Nuggets game on the specified date.
    """
    date = "2025-04-19"
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}?key={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] == "LAC" and game['AwayTeam'] == "DEN" or game['HomeTeam'] == "DEN" and game['AwayTeam'] == "LAC":
                logger.info("Game found: Clippers vs. Nuggets")
                return game
        logger.info("No game found for Clippers vs. Nuggets on the specified date.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch NBA game data: {e}")
        return None

def resolve_market(game):
    """
    Resolves the market based on the game data.
    """
    if not game:
        return "p4"  # Too early to resolve or no data available
    
    if game['Status'] == "Final":
        if game['HomeTeam'] == "LAC" and game['HomeTeamScore'] > game['AwayTeamScore']:
            return RESOLUTION_MAP["LAC"]
        elif game['AwayTeam'] == "LAC" and game['AwayTeamScore'] > game['HomeTeamScore']:
            return RESOLUTION_MAP["LAC"]
        else:
            return RESOLUTION_MAP["DEN"]
    elif game['Status'] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Postponed":
        return "p4"  # Market remains open until the game is completed
    else:
        return "p4"  # Game not final yet

def main():
    """
    Main function to fetch NBA game data and resolve the market.
    """
    game_data = fetch_nba_game_data()
    resolution = resolve_market(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()