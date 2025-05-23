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
    "SEA": "p2",  # Seattle Mariners win maps to p2
    "CIN": "p1",  # Cincinnati Reds win maps to p1
    "50-50": "p3",  # Canceled or no make-up game maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
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
    Fetches game data for the specified date and teams.
    """
    date = datetime.now().strftime("%Y-%m-%d")  # Today's date
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] == 'SEA' and game['AwayTeam'] == 'CIN' or game['HomeTeam'] == 'CIN' and game['AwayTeam'] == 'SEA':
                return game
        return None
    except requests.RequestException as e:
        logger.error(f"Error fetching game data: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return "p4"  # No game data found

    if game['Status'] == 'Final':
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        
        return RESOLUTION_MAP.get(winner, "p4")
    elif game['Status'] == 'Canceled':
        return "p3"
    elif game['Status'] in ['Scheduled', 'InProgress', 'Delayed', 'Postponed']:
        return "p4"
    else:
        return "p4"

def main():
    """
    Main function to determine the resolution of the MLB game.
    """
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()