import os
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Constants
GAME_DATE = "2025-06-14"
PLAYER_NAME = "Matthew Tkachuk"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}
GAME_ID = "552357"

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_game_data():
    """
    Fetches game data from the NHL API.
    """
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_formatted}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['GameID'] == GAME_ID:
                return game
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching game data: {e}")
        return None

def check_player_goals(game_data):
    """
    Checks if the specified player scored a goal in the game.
    """
    if not game_data:
        return "p4"  # Unable to retrieve game data

    if datetime.now() < datetime.strptime(GAME_DATE + " 23:59:59", "%Y-%m-%d %H:%M:%S"):
        return "p4"  # Game has not been completed yet

    if game_data['Status'] != 'Final':
        return "p3"  # Game not completed by the specified future date

    player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_data['GameID']}"
    try:
        response = requests.get(player_stats_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == PLAYER_NAME and stat['Goals'] > 0:
                return "p2"  # Player scored a goal
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching player stats: {e}")
        return "p4"  # Error in fetching data

    return "p1"  # Player did not score a goal

if __name__ == "__main__":
    game_data = get_game_data()
    result = check_player_goals(game_data)
    print(f"recommendation: {result}")