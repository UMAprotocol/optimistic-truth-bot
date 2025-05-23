import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "LAC": "p2",  # LA Clippers win maps to p2
    "DEN": "p1",  # Denver Nuggets win maps to p1
    "50-50": "p3",  # Game canceled or unresolved maps to p3
    "Too early to resolve": "p4",  # Game not yet played or no data available maps to p4
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nba_game_data():
    """
    Fetches NBA game data for the Clippers vs. Nuggets game scheduled on 2025-04-21.
    """
    date = "2025-04-21"
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}?key={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] == 'LAC' and game['AwayTeam'] == 'DEN' or game['HomeTeam'] == 'DEN' and game['AwayTeam'] == 'LAC':
                logging.info("Game found: Clippers vs. Nuggets")
                if game['Status'] == 'Final':
                    home_team = game['HomeTeam']
                    away_team = game['AwayTeam']
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    
                    if home_score > away_score:
                        winner = home_team
                    else:
                        winner = away_team
                    
                    return RESOLUTION_MAP.get(winner, "p4")
                elif game['Status'] == 'Canceled':
                    return RESOLUTION_MAP["50-50"]
                elif game['Status'] in ['Scheduled', 'InProgress', 'Delayed', 'Postponed']:
                    return RESOLUTION_MAP["Too early to resolve"]
        return RESOLUTION_MAP["Too early to resolve"]
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch game data: {e}")
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    resolution = fetch_nba_game_data()
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()