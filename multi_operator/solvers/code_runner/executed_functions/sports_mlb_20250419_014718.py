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
    "NYY": "p2",  # New York Yankees win
    "TBR": "p1",  # Tampa Bay Rays win
    "50-50": "p3",  # Game canceled or postponed without resolution
    "Too early to resolve": "p4",  # Game not yet played or no data available
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_data():
    """
    Fetches game data for the specified MLB game between New York Yankees and Tampa Bay Rays.
    """
    date = "2025-04-18"
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] in ['NYY', 'TBR'] and game['AwayTeam'] in ['NYY', 'TBR']:
                return game
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching game data: {e}")
        return None

def resolve_market(game):
    """
    Resolves the market based on the game data.
    """
    if not game:
        return "recommendation: p4"  # No data available

    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        
        return f"recommendation: {RESOLUTION_MAP.get(winner, 'p3')}"
    elif game['Status'] in ["Canceled", "Postponed"]:
        return "recommendation: p3"
    else:
        return "recommendation: p4"

def main():
    game_data = fetch_game_data()
    result = resolve_market(game_data)
    print(result)

if __name__ == "__main__":
    main()