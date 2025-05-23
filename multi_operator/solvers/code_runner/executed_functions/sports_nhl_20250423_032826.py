import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "FLA": "p2",  # Florida Panthers
    "TBL": "p1",  # Tampa Bay Lightning
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nhl_game_data():
    """
    Fetches NHL game data for the specified game between Florida Panthers and Tampa Bay Lightning.
    """
    date = "2025-04-22"
    team1 = "FLA"
    team2 = "TBL"
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}?key={NHL_API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        winner = game['HomeTeam']
                    else:
                        winner = game['AwayTeam']
                    
                    return RESOLUTION_MAP[winner]
                elif game['Status'] == "Canceled":
                    return RESOLUTION_MAP["50-50"]
                elif game['Status'] == "Postponed":
                    return RESOLUTION_MAP["Too early to resolve"]
                else:
                    return RESOLUTION_MAP["Too early to resolve"]
        return RESOLUTION_MAP["Too early to resolve"]
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    resolution = fetch_nhl_game_data()
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()