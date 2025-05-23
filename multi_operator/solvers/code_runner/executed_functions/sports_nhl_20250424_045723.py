import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "DAL": "p2",  # Dallas Stars
    "COL": "p1",  # Colorado Avalanche
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_nhl_game_data():
    """
    Fetches NHL game data for the specified game and determines the resolution.
    """
    # Game details
    game_date = "2025-04-23"
    team1 = "DAL"  # Dallas Stars
    team2 = "COL"  # Colorado Avalanche

    # API endpoints
    primary_url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={NHL_API_KEY}"
    proxy_url = f"https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/nhl/GamesByDate/{game_date}"

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, timeout=10)
        if response.status_code != 200:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(primary_url, timeout=10)
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
        return "recommendation: p4"  # No matching game found
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch or process game data: {e}")
        return "recommendation: p4"

def main():
    result = fetch_nhl_game_data()
    print(result)

if __name__ == "__main__":
    main()