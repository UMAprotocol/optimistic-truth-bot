import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "LAD": "p2",  # Los Angeles Dodgers win
    "TEX": "p1",  # Texas Rangers win
    "50-50": "p3",  # Game canceled or postponed without resolution
    "Too early to resolve": "p4",  # Game not yet played or no data available
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_data():
    """
    Fetches game data for the specified MLB game between Los Angeles Dodgers and Texas Rangers.
    """
    date = datetime.now().strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] == 'LAD' and game['AwayTeam'] == 'TEX' or game['HomeTeam'] == 'TEX' and game['AwayTeam'] == 'LAD':
                return game
        return None
    except requests.RequestException as e:
        logging.error(f"Error fetching game data: {e}")
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
        
        if winner == 'LAD':
            return "p2"  # Dodgers win
        elif winner == 'TEX':
            return "p1"  # Rangers win
    elif game['Status'] in ['Canceled', 'Postponed']:
        return "p3"  # Game canceled or postponed

    return "p4"  # Game not final or no clear outcome

def main():
    """
    Main function to determine the outcome of the MLB game between Los Angeles Dodgers and Texas Rangers.
    """
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()