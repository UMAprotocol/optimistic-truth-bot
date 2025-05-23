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
    "50-50": "p3",  # Game canceled or unresolved
    "Too early to resolve": "p4",  # Game not yet played or no data available
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_data(date):
    """
    Fetches game data for the specified date.
    """
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        return games
    except requests.RequestException as e:
        logging.error(f"Failed to fetch game data: {e}")
        return None

def resolve_market(games):
    """
    Resolves the market based on the game data.
    """
    for game in games:
        if game['HomeTeam'] == 'LAD' or game['AwayTeam'] == 'LAD':
            if game['HomeTeam'] == 'TEX' or game['AwayTeam'] == 'TEX':
                if game['Status'] == 'Final':
                    home_score = game['HomeTeamRuns']
                    away_score = game['AwayTeamRuns']
                    if home_score > away_score:
                        winner = game['HomeTeam']
                    else:
                        winner = game['AwayTeam']
                    return RESOLUTION_MAP.get(winner, "p4")
                elif game['Status'] in ['Canceled', 'Postponed']:
                    return RESOLUTION_MAP["50-50"]
                else:
                    return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to determine the outcome of the Los Angeles Dodgers vs. Texas Rangers game.
    """
    game_date = "2025-04-19"
    games = fetch_game_data(game_date)
    if games is None:
        print("recommendation: p4")
    else:
        resolution = resolve_market(games)
        print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()