import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "EDM": "p2",  # Edmonton Oilers
    "LAK": "p1",  # Los Angeles Kings
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
        if response.status_code != 200:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(primary_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch NHL game data: {e}")
        return None

def resolve_market(games):
    """
    Resolves the market based on the game data.
    """
    for game in games:
        if game['HomeTeam'] == "EDM" or game['AwayTeam'] == "EDM":
            if game['HomeTeam'] == "LAK" or game['AwayTeam'] == "LAK":
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        winner = game['HomeTeam']
                    else:
                        winner = game['AwayTeam']
                    
                    if winner == "EDM":
                        return "recommendation: p2"  # Oilers win
                    elif winner == "LAK":
                        return "recommendation: p1"  # Kings win
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"  # Game canceled, resolve 50-50
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"  # Game postponed, too early to resolve
    return "recommendation: p4"  # No relevant game found or game not yet completed

def main():
    """
    Main function to determine the outcome of the Oilers vs. Kings game.
    """
    game_date = "2025-04-23"
    games = fetch_nhl_game_data(game_date)
    if games:
        result = resolve_market(games)
    else:
        result = "recommendation: p4"  # Unable to fetch data or no games on the specified date
    print(result)

if __name__ == "__main__":
    main()