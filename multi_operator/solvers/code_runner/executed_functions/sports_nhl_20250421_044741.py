import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "MIN": "p2",  # Minnesota Wild
    "VGK": "p1",  # Vegas Golden Knights
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

def fetch_nhl_game_data(game_date):
    """
    Fetches NHL game data for a specific date.
    """
    primary_url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={NHL_API_KEY}"
    proxy_url = f"https://minimal-ubuntu-production.up.railway.app/binance-proxy/v3/nhl/scores/json/GamesByDate/{game_date}?key={NHL_API_KEY}"
    
    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        logger.info("Proxy failed, trying primary endpoint")
        try:
            # Fallback to primary endpoint
            response = requests.get(primary_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch data from primary endpoint: {e}")
            return None
    
    games = response.json()
    return games

def resolve_market(games):
    """
    Resolves the market based on the game data.
    """
    for game in games:
        if game['HomeTeam'] == 'MIN' or game['AwayTeam'] == 'MIN':
            if game['HomeTeam'] == 'VGK' or game['AwayTeam'] == 'VGK':
                if game['Status'] == 'Final':
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        winner = game['HomeTeam']
                    else:
                        winner = game['AwayTeam']
                    
                    return "recommendation: " + RESOLUTION_MAP[winner]
                elif game['Status'] == 'Postponed':
                    return "recommendation: p4"  # Market remains open
                elif game['Status'] == 'Canceled':
                    return "recommendation: p3"  # Resolve 50-50
    return "recommendation: p4"  # No relevant game found or game not yet played

def main():
    """
    Main function to determine the outcome of the NHL game.
    """
    game_date = "2025-04-20"
    games = fetch_nhl_game_data(game_date)
    if games:
        result = resolve_market(games)
    else:
        result = "recommendation: p4"  # Unable to fetch game data or no games on the specified date
    print(result)

if __name__ == "__main__":
    main()