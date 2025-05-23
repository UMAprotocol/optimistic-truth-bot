import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "MIN": "p2",  # Minnesota Wild
    "VGK": "p1",  # Vegas Golden Knights
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

def fetch_game_data(date):
    """
    Fetches game data for the specified date.
    Args:
        date: Game date in YYYY-MM-DD format
    Returns:
        Game data dictionary or None if not found
    """
    headers = {'Ocp-Apim-Subscription-Key': NHL_API_KEY}
    url = f"{PROXY_ENDPOINT}/{date}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        games = response.json()
        return games
    except requests.exceptions.RequestException:
        logging.warning("Proxy failed, falling back to primary endpoint")
        url = f"{PRIMARY_ENDPOINT}/{date}?key={NHL_API_KEY}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            games = response.json()
            return games
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch data from primary endpoint: {e}")
            return None

def determine_resolution(games):
    """
    Determines the resolution based on the game's status and outcome.
    Args:
        games: List of games data
    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    for game in games:
        if game['HomeTeam'] == "MIN" or game['AwayTeam'] == "MIN":
            if game['HomeTeam'] == "VGK" or game['AwayTeam'] == "VGK":
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        winner = game['HomeTeam']
                    else:
                        winner = game['AwayTeam']
                    
                    return RESOLUTION_MAP.get(winner, "p4")
                elif game['Status'] == "Canceled":
                    return "p3"
                elif game['Status'] == "Postponed":
                    return "p4"
    return "p4"

def main():
    """
    Main function to determine the resolution of the NHL game.
    """
    date = "2025-04-20"
    games = fetch_game_data(date)
    if games is None:
        print("recommendation: p4")
    else:
        resolution = determine_resolution(games)
        print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()