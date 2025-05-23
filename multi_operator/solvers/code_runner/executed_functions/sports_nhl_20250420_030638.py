import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

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
    date = "2025-04-19"
    game_url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}?key={API_KEY}"
    
    try:
        response = requests.get(game_url, timeout=10)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] == "MIN" and game['AwayTeam'] == "LAL" or game['HomeTeam'] == "LAL" and game['AwayTeam'] == "MIN":
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return RESOLUTION_MAP[game['HomeTeam']]
                    else:
                        return RESOLUTION_MAP[game['AwayTeam']]
                elif game['Status'] == "Canceled":
                    return RESOLUTION_MAP["50-50"]
                elif game['Status'] in ["Scheduled", "InProgress"]:
                    return RESOLUTION_MAP["Too early to resolve"]
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch NBA game data: {e}")
        return RESOLUTION_MAP["Too early to resolve"]

    return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to determine the outcome of the NBA game between Timberwolves and Lakers.
    """
    resolution = fetch_nba_game_data()
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()