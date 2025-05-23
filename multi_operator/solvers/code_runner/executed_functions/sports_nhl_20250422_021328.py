import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "MTL": "p2",  # Montreal Canadiens
    "WSH": "p1",  # Washington Capitals
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nhl_game_data():
    """
    Fetches NHL game data for the specified game and determines the resolution.
    """
    # Game details
    game_date = "2025-04-21"
    team1 = "MTL"  # Montreal Canadiens
    team2 = "WSH"  # Washington Capitals

    # API URL
    primary_url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={NHL_API_KEY}"
    proxy_url = f"https://minimal-ubuntu-production.up.railway.app/sportsdata-proxy/nhl/GamesByDate/{game_date}?key={NHL_API_KEY}"

    # Try proxy endpoint first
    try:
        response = requests.get(proxy_url, timeout=10)
        response.raise_for_status()
    except (requests.RequestException, requests.Timeout):
        logging.warning("Proxy failed, falling back to primary endpoint.")
        try:
            response = requests.get(primary_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"Failed to fetch data from primary endpoint: {e}")
            return "recommendation: p4"

    # Process the response
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
                
                return f"recommendation: {RESOLUTION_MAP[winner]}"
            elif game['Status'] == "Canceled":
                return "recommendation: p3"
            elif game['Status'] == "Postponed":
                return "recommendation: p4"
            else:
                return "recommendation: p4"

    return "recommendation: p4"

def main():
    result = fetch_nhl_game_data()
    print(result)

if __name__ == "__main__":
    main()