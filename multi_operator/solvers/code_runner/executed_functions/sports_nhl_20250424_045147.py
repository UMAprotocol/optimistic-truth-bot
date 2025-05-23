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
    proxy_url = f"https://minimal-ubuntu-production.up.railway.app/binance-proxy/v3/nhl/scores/json/GamesByDate/{game_date}?key={NHL_API_KEY}"
    
    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        logging.info("Proxy failed, trying primary endpoint")
        response = requests.get(primary_url, timeout=10)
        response.raise_for_status()

    return response.json()

def resolve_market(games):
    """
    Resolves the market based on the game data.
    """
    for game in games:
        if game['HomeTeam'] == "EDM" or game['AwayTeam'] == "EDM":
            if game['Status'] == "Final":
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score and game['HomeTeam'] == "EDM":
                    return "recommendation: " + RESOLUTION_MAP["EDM"]
                elif away_score > home_score and game['AwayTeam'] == "EDM":
                    return "recommendation: " + RESOLUTION_MAP["EDM"]
                elif home_score > away_score and game['HomeTeam'] == "LAK":
                    return "recommendation: " + RESOLUTION_MAP["LAK"]
                elif away_score > home_score and game['AwayTeam'] == "LAK":
                    return "recommendation: " + RESOLUTION_MAP["LAK"]
            elif game['Status'] == "Postponed":
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
            elif game['Status'] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to fetch NHL game data and resolve the market.
    """
    game_date = "2025-04-23"
    try:
        games = fetch_nhl_game_data(game_date)
        result = resolve_market(games)
        print(result)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print("recommendation: " + RESOLUTION_MAP["Too early to resolve"])

if __name__ == "__main__":
    main()