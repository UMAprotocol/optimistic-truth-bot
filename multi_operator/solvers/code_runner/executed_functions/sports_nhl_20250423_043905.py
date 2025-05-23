import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
RESOLUTION_MAP = {
    "MIN": "p2",  # Timberwolves win
    "LAL": "p1",  # Lakers win
    "50-50": "p3",  # Game canceled or unresolved
    "Too early to resolve": "p4",  # Game not yet played or no data
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nba_game_data():
    """
    Fetches NBA game data for the Timberwolves vs. Lakers game on the specified date.
    """
    game_date = "2025-04-22"
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{game_date}?key={NBA_API_KEY}"
    
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
    if not game:
        return "recommendation: p4"  # No data available

    if game['Status'] == "Scheduled":
        return "recommendation: p4"  # Game has not yet been played
    elif game['Status'] == "Final":
        if game['HomeTeam'] == "MIN" and game['HomeTeamScore'] > game['AwayTeamScore']:
            return "recommendation: p2"  # Timberwolves win
        elif game['HomeTeam'] == "LAL" and game['HomeTeamScore'] > game['AwayTeamScore']:
            return "recommendation: p1"  # Lakers win
        elif game['AwayTeam'] == "MIN" and game['AwayTeamScore'] > game['HomeTeamScore']:
            return "recommendation: p2"  # Timberwolves win
        elif game['AwayTeam'] == "LAL" and game['AwayTeamScore'] > game['HomeTeamScore']:
            return "recommendation: p1"  # Lakers win
    elif game['Status'] in ["Canceled", "Postponed"]:
        return "recommendation: p3"  # Game canceled or postponed

    return "recommendation: p3"  # Default to 50-50 if status is unclear

def main():
    """
    Main function to fetch NBA game data and resolve the market.
    """
    game_data = fetch_nba_game_data()
    resolution = resolve_market(game_data)
    print(resolution)

if __name__ == "__main__":
    main()