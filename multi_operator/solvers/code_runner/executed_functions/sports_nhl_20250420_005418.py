import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "DET": "p2",  # Detroit Pistons win maps to p2
    "NYK": "p1",  # New York Knicks win maps to p1
    "50-50": "p3",  # Canceled or no make-up game maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_game_result():
    """
    Fetches the result of the NBA game between Detroit Pistons and New York Knicks.
    """
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/2025-04-19?key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] == 'DET' and game['AwayTeam'] == 'NYK' or game['HomeTeam'] == 'NYK' and game['AwayTeam'] == 'DET':
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
                else:
                    return RESOLUTION_MAP["Too early to resolve"]
        return RESOLUTION_MAP["Too early to resolve"]
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch game data: {e}")
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to determine the resolution of the NBA game.
    """
    resolution = fetch_game_result()
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()