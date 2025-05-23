import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "COL": "p2",  # Colorado Avalanche
    "DAL": "p1",  # Dallas Stars
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nhl_game_data():
    """
    Fetches NHL game data for the specified game and date.
    """
    date = "2025-04-19"
    team1 = "COL"  # Colorado Avalanche
    team2 = "DAL"  # Dallas Stars
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
                    
                    return "recommendation: " + RESOLUTION_MAP[winner]
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"
                else:
                    return "recommendation: p4"
        return "recommendation: p4"  # No matching game found or other statuses
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch NHL game data: {e}")
        return "recommendation: p4"

def main():
    result = fetch_nhl_game_data()
    print(result)

if __name__ == "__main__":
    main()