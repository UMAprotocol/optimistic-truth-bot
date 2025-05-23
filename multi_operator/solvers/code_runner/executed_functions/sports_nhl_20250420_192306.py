import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants for API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy/GamesByDate/"

# Constants for resolution mapping
RESOLUTION_MAP = {
    "MEM": "p2",  # Memphis Grizzlies
    "OKC": "p1",  # Oklahoma City Thunder
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_data(date):
    """
    Fetches NBA game data for the specified date.
    Args:
        date: Game date in YYYY-MM-DD format
    Returns:
        Game data dictionary or None if not found
    """
    headers = {"Ocp-Apim-Subscription-Key": API_KEY}
    url = f"{PROXY_ENDPOINT}{date}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        games = response.json()
        logging.info(f"Data fetched successfully from proxy endpoint for date {date}")
        return games
    except requests.exceptions.RequestException:
        logging.warning("Proxy endpoint failed, falling back to primary endpoint")
        url = f"{PRIMARY_ENDPOINT}{date}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            games = response.json()
            logging.info(f"Data fetched successfully from primary endpoint for date {date}")
            return games
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch data from primary endpoint: {e}")
            return None

def determine_resolution(games):
    """
    Determines the resolution based on the game's outcome.
    Args:
        games: List of games data
    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    for game in games:
        if game['HomeTeam'] == 'MEM' or game['AwayTeam'] == 'MEM':
            if game['Status'] == 'Final':
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score and game['HomeTeam'] == 'MEM':
                    return RESOLUTION_MAP['MEM']
                elif away_score > home_score and game['AwayTeam'] == 'MEM':
                    return RESOLUTION_MAP['MEM']
                elif home_score > away_score and game['HomeTeam'] == 'OKC':
                    return RESOLUTION_MAP['OKC']
                elif away_score > home_score and game['AwayTeam'] == 'OKC':
                    return RESOLUTION_MAP['OKC']
            elif game['Status'] == 'Canceled':
                return RESOLUTION_MAP['50-50']
            elif game['Status'] == 'Postponed':
                return RESOLUTION_MAP['Too early to resolve']
    return RESOLUTION_MAP['Too early to resolve']

def main():
    """
    Main function to query NBA game data and determine the resolution.
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