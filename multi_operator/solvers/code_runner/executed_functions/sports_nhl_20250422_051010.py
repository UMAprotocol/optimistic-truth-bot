import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "COL": "p2",  # Colorado Avalanche
    "DAL": "p1",  # Dallas Stars
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_game_data(api_key, game_date, team1, team2):
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date}?key={api_key}"
    proxy_url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{game_date}?key={api_key}"
    
    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, timeout=10)
        if response.status_code != 200:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch game data: {e}")
        return None

def resolve_market(game):
    if not game:
        return "p4"  # No game data found, too early to resolve
    
    if game['Status'] == "Final":
        if game['HomeTeamScore'] > game['AwayTeamScore']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        
        return RESOLUTION_MAP.get(winner, "p3")  # Default to 50-50 if winner not in map
    elif game['Status'] == "Canceled":
        return "p3"  # Game canceled, resolve as 50-50
    else:
        return "p4"  # Game not final or canceled, too early to resolve

def main():
    game_date = "2025-04-21"
    team1 = "COL"  # Colorado Avalanche
    team2 = "DAL"  # Dallas Stars
    
    if not NHL_API_KEY:
        logging.error("NHL API key is not set. Please check your .env file.")
        print("recommendation: p4")
        return
    
    game = fetch_game_data(NHL_API_KEY, game_date, team1, team2)
    resolution = resolve_market(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()