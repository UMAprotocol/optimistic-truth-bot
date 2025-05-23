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

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

def fetch_game_data(api_key, game_date):
    """
    Fetches game data for the specified date.
    """
    url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{game_date}?key={api_key}"
    primary_url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date}?key={api_key}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        logging.warning("Proxy failed, falling back to primary endpoint.")
        response = requests.get(primary_url, timeout=10)
        response.raise_for_status()

    return response.json()

def determine_resolution(games):
    """
    Determines the resolution based on the game's outcome.
    """
    for game in games:
        if game['Day'] == "2025-04-22" and game['Status'] == "Final":
            if game['HomeTeam'] == "FLA" and game['AwayTeam'] == "TBL":
                if game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "recommendation: " + RESOLUTION_MAP["FLA"]
                elif game['HomeTeamScore'] < game['AwayTeamScore']:
                    return "recommendation: " + RESOLUTION_MAP["TBL"]
            elif game['HomeTeam'] == "TBL" and game['AwayTeam'] == "FLA":
                if game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "recommendation: " + RESOLUTION_MAP["TBL"]
                elif game['HomeTeamScore'] < game['AwayTeamScore']:
                    return "recommendation: " + RESOLUTION_MAP["FLA"]
        elif game['Status'] == "Canceled":
            return "recommendation: " + RESOLUTION_MAP["50-50"]
        elif game['Status'] == "Postponed":
            return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to fetch NHL game data and determine the resolution.
    """
    game_date = "2025-04-22"
    games = fetch_game_data(NHL_API_KEY, game_date)
    resolution = determine_resolution(games)
    print(resolution)

if __name__ == "__main__":
    main()