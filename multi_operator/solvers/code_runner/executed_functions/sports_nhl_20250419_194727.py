import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "MIL": "p2",  # Milwaukee Bucks win maps to p2
    "IND": "p1",  # Indiana Pacers win maps to p1
    "50-50": "p3",  # Canceled or unresolved maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nba_game_data(date):
    """
    Fetches NBA game data for the specified date.
    
    Args:
        date (str): Game date in YYYY-MM-DD format
    
    Returns:
        dict: Game data or None if not found
    """
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}?key={NBA_API_KEY}"
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
    
    Args:
        games (list): List of games data
    
    Returns:
        str: Resolution string (p1, p2, p3, or p4)
    """
    for game in games:
        if game['HomeTeam'] == 'MIL' and game['AwayTeam'] == 'IND' or game['HomeTeam'] == 'IND' and game['AwayTeam'] == 'MIL':
            if game['Status'] == 'Final':
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                return RESOLUTION_MAP.get(winner, "p4")
            elif game['Status'] == 'Canceled':
                return "p3"
            elif game['Status'] == 'Postponed':
                return "p4"
    return "p4"

def main():
    """
    Main function to determine the resolution of the NBA game market.
    """
    game_date = "2025-04-19"
    games = fetch_nba_game_data(game_date)
    if games is None:
        print("recommendation: p4")
    else:
        resolution = resolve_market(games)
        print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()