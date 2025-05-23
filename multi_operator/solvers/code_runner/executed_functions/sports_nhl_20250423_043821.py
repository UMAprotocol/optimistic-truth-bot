import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "MIN": "p2",  # Timberwolves win maps to p2
    "LAL": "p1",  # Lakers win maps to p1
    "50-50": "p3",  # Game canceled or unresolved maps to p3
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nba_game_data():
    """
    Fetches NBA game data for the Timberwolves vs. Lakers game on the specified date.
    """
    date = "2025-04-22"
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}?key={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] == "MIN" and game['AwayTeam'] == "LAL" or game['HomeTeam'] == "LAL" and game['AwayTeam'] == "MIN":
                logging.info("Game found: Timberwolves vs. Lakers")
                return game
        logging.info("No game found for Timberwolves vs. Lakers on the specified date.")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch NBA game data: {e}")
        return None

def resolve_market(game):
    """
    Resolves the market based on the game data.
    """
    if game is None:
        return "recommendation: p3"  # No game data found, resolve as 50-50

    if game['Status'] == "Final":
        if game['HomeTeam'] == "MIN" and game['HomeTeamScore'] > game['AwayTeamScore']:
            return "recommendation: p2"  # Timberwolves win
        elif game['HomeTeam'] == "LAL" and game['HomeTeamScore'] > game['AwayTeamScore']:
            return "recommendation: p1"  # Lakers win
        else:
            return "recommendation: p3"  # Game tied or other team won
    elif game['Status'] in ["Canceled", "Postponed"]:
        return "recommendation: p3"  # Game not played or postponed, resolve as 50-50
    else:
        return "recommendation: p3"  # Game not final, resolve as 50-50

def main():
    """
    Main function to fetch NBA game data and resolve the market.
    """
    game_data = fetch_nba_game_data()
    resolution = resolve_market(game_data)
    print(resolution)

if __name__ == "__main__":
    main()