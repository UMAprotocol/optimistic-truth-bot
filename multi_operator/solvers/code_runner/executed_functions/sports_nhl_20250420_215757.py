import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
RESOLUTION_MAP = {
    "ORL": "p2",  # Orlando Magic
    "BOS": "p1",  # Boston Celtics
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_nba_game_data():
    """
    Fetches NBA game data for the Orlando Magic vs. Boston Celtics game on the specified date.
    """
    date = "2025-04-20"
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}?key={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] == "ORL" and game['AwayTeam'] == "BOS" or game['HomeTeam'] == "BOS" and game['AwayTeam'] == "ORL":
                if game['Status'] == "Final":
                    home_team = game['HomeTeam']
                    away_team = game['AwayTeam']
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    
                    if home_score > away_score:
                        winner = home_team
                    else:
                        winner = away_team
                    
                    return RESOLUTION_MAP[winner]
                elif game['Status'] == "Canceled":
                    return RESOLUTION_MAP["50-50"]
                elif game['Status'] == "Postponed":
                    return RESOLUTION_MAP["Too early to resolve"]
                else:
                    return RESOLUTION_MAP["Too early to resolve"]
        return RESOLUTION_MAP["Too early to resolve"]
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch NBA game data: {e}")
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to determine the outcome of the NBA game between Orlando Magic and Boston Celtics.
    """
    resolution = fetch_nba_game_data()
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()