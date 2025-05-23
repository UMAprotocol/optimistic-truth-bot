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
    "Dodgers": "p2",  # Los Angeles Dodgers win maps to p2
    "Rangers": "p1",  # Texas Rangers win maps to p1
    "50-50": "p3",    # Tie or undetermined maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
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
    Fetches game data for the specified MLB game between Los Angeles Dodgers and Texas Rangers.
    
    Returns:
        Game data dictionary or None if not found
    """
    date = "2025-04-18"
    team1_name = "Los Angeles Dodgers"
    team2_name = "Texas Rangers"
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] == 'LAD' and game['AwayTeam'] == 'TEX' or game['HomeTeam'] == 'TEX' and game['AwayTeam'] == 'LAD':
                return game
        logger.info("No game found for the specified teams on the specified date.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch game data: {e}")
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
        return "recommendation: p4"

    status = game.get("Status")
    if status == "Final":
        home_team = game.get("HomeTeam")
        away_team = game.get("AwayTeam")
        home_score = game.get("HomeTeamRuns")
        away_score = game.get("AwayTeamRuns")
        
        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team
        
        if winner == 'LAD':
            return "recommendation: p2"
        elif winner == 'TEX':
            return "recommendation: p1"
    elif status == "Canceled":
        return "recommendation: p3"
    elif status == "Postponed":
        return "recommendation: p4"
    else:
        return "recommendation: p4"

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(resolution)

if __name__ == "__main__":
    main()