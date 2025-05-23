import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "MIL": "p2",  # Milwaukee Bucks win maps to p2
    "IND": "p1",  # Indiana Pacers win maps to p1
    "50-50": "p3",  # Game canceled or unresolved maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nba_game_data():
    """
    Fetches NBA game data for the Milwaukee Bucks vs. Indiana Pacers game on the specified date.
    """
    date = "2025-04-22"
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}?key={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] == "MIL" and game['AwayTeam'] == "IND" or game['HomeTeam'] == "IND" and game['AwayTeam'] == "MIL":
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        winner = game['HomeTeam']
                    else:
                        winner = game['AwayTeam']
                    return RESOLUTION_MAP.get(winner, "p4")
                elif game['Status'] == "Canceled":
                    return RESOLUTION_MAP["50-50"]
                elif game['Status'] in ["Scheduled", "InProgress", "Delayed", "Postponed"]:
                    return RESOLUTION_MAP["Too early to resolve"]
        return RESOLUTION_MAP["Too early to resolve"]
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch NBA game data: {e}")
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to determine the resolution of the NBA game between Milwaukee Bucks and Indiana Pacers.
    """
    resolution = fetch_nba_game_data()
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()