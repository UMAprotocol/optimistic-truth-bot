import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "ORL": "p2",  # Orlando Magic
    "BOS": "p1",  # Boston Celtics
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nba_game_data():
    """
    Fetches NBA game data for the Orlando Magic vs. Boston Celtics game scheduled for April 23, 2025.
    """
    date = "2025-04-23"
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}?key={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] == "ORL" and game['AwayTeam'] == "BOS" or game['HomeTeam'] == "BOS" and game['AwayTeam'] == "ORL":
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        winner = game['HomeTeam']
                    else:
                        winner = game['AwayTeam']
                    
                    if winner == "ORL":
                        return "recommendation: p2"
                    elif winner == "BOS":
                        return "recommendation: p1"
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"
                elif game['Status'] in ["Scheduled", "InProgress", "Delayed", "Postponed"]:
                    return "recommendation: p4"
        return "recommendation: p4"  # No matching game found or game not yet played
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch NBA game data: {e}")
        return "recommendation: p4"

def main():
    """
    Main function to determine the outcome of the NBA game between Orlando Magic and Boston Celtics.
    """
    result = fetch_nba_game_data()
    print(result)

if __name__ == "__main__":
    main()