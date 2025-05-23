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

def fetch_nhl_game_data(game_date):
    """
    Fetches NHL game data for a specific date.
    """
    primary_url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={NHL_API_KEY}"
    proxy_url = f"https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/nhl/GamesByDate/{game_date}?key={NHL_API_KEY}"

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        logging.info("Proxy failed, trying primary endpoint.")
        # Fallback to primary endpoint if proxy fails
        response = requests.get(primary_url, timeout=10)
        response.raise_for_status()

    return response.json()

def resolve_market(games):
    """
    Resolves the market based on the game data.
    """
    for game in games:
        if game['HomeTeam'] == 'WSH' and game['AwayTeam'] == 'MTL' or game['HomeTeam'] == 'MTL' and game['AwayTeam'] == 'WSH':
            if game['Status'] == 'Final':
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                
                return f"recommendation: {RESOLUTION_MAP[winner]}"
            elif game['Status'] == 'Canceled':
                return f"recommendation: {RESOLUTION_MAP['50-50']}"
            elif game['Status'] == 'Postponed':
                return f"recommendation: {RESOLUTION_MAP['Too early to resolve']}"
            else:
                return f"recommendation: {RESOLUTION_MAP['Too early to resolve']}"

    return f"recommendation: {RESOLUTION_MAP['Too early to resolve']}"

def main():
    """
    Main function to determine the outcome of the Canadiens vs. Capitals game.
    """
    game_date = "2025-04-23"
    try:
        games = fetch_nhl_game_data(game_date)
        result = resolve_market(games)
        print(result)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print(f"recommendation: {RESOLUTION_MAP['Too early to resolve']}")

if __name__ == "__main__":
    main()