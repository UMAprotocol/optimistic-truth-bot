import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "MIL": "p2",  # Milwaukee Bucks win
    "IND": "p1",  # Indiana Pacers win
    "50-50": "p3",  # Game canceled with no make-up
    "Too early to resolve": "p4",  # Game not yet played or no data available
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nba_game_data(date):
    """
    Fetches NBA game data for a specific date.
    """
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}?key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        return games
    except requests.RequestException as e:
        logging.error(f"Failed to fetch NBA game data: {e}")
        return None

def resolve_market(games):
    """
    Resolves the market based on the game data.
    """
    for game in games:
        if game['HomeTeam'] == 'MIL' or game['AwayTeam'] == 'MIL':
            if game['HomeTeam'] == 'IND' or game['AwayTeam'] == 'IND':
                if game['Status'] == 'Final':
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        winner = game['HomeTeam']
                    else:
                        winner = game['AwayTeam']
                    return RESOLUTION_MAP.get(winner, "p4")
                elif game['Status'] == 'Canceled':
                    return RESOLUTION_MAP["50-50"]
                elif game['Status'] in ['Scheduled', 'InProgress']:
                    return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to determine the outcome of the Bucks vs. Pacers game.
    """
    game_date = "2025-04-22"
    games = fetch_nba_game_data(game_date)
    if games is None:
        print("recommendation: p4")
    else:
        resolution = resolve_market(games)
        print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()