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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

def fetch_game_data(api_key, game_date):
    """
    Fetches game data for the specified date.
    """
    url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{game_date}?key={api_key}"
    fallback_url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date}?key={api_key}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        logging.warning("Proxy failed, falling back to primary endpoint.")
        response = requests.get(fallback_url, timeout=10)
        response.raise_for_status()

    games = response.json()
    return games

def determine_resolution(games):
    """
    Determines the resolution based on the game's outcome.
    """
    for game in games:
        if game['HomeTeam'] == "MIN" or game['AwayTeam'] == "MIN":
            if game['Status'] == "Final":
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score and game['HomeTeam'] == "MIN":
                    return "recommendation: " + RESOLUTION_MAP["MIN"]
                elif away_score > home_score and game['AwayTeam'] == "MIN":
                    return "recommendation: " + RESOLUTION_MAP["MIN"]
                elif home_score > away_score and game['HomeTeam'] == "VGK":
                    return "recommendation: " + RESOLUTION_MAP["VGK"]
                elif away_score > home_score and game['AwayTeam'] == "VGK":
                    return "recommendation: " + RESOLUTION_MAP["VGK"]
            elif game['Status'] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            elif game['Status'] == "Postponed":
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to determine the resolution of the NHL game.
    """
    game_date = "2025-04-22"
    if not NHL_API_KEY:
        logging.error("NHL API key is not set. Please check your .env file.")
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    games = fetch_game_data(NHL_API_KEY, game_date)
    resolution = determine_resolution(games)
    print(resolution)

if __name__ == "__main__":
    main()