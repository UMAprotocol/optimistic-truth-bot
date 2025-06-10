import os
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Constants
GAME_DATE = "2025-05-28"
TEAM_NAME = "Oklahoma City Thunder"
PLAYER_NAME = "Shai Gilgeous-Alexander"
MIN_POINTS = 34

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_game_data():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%b-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_formatted}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if TEAM_NAME in (game['HomeTeam'], game['AwayTeam']):
                return game
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching game data: {e}")
    return None

def get_player_stats(game_id):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == PLAYER_NAME:
                return stat
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching player stats: {e}")
    return None

def resolve_market():
    game = get_game_data()
    if not game:
        return "recommendation: p1"  # No game found, resolve to "No"

    if game['Status'] != 'Final':
        return "recommendation: p1"  # Game not completed, resolve to "No"

    if game['Winner'] != TEAM_NAME:
        return "recommendation: p1"  # Thunder did not win, resolve to "No"

    player_stats = get_player_stats(game['GameID'])
    if not player_stats:
        return "recommendation: p1"  # Player stats not found, resolve to "No"

    points_scored = player_stats.get('Points', 0)
    if points_scored >= MIN_POINTS:
        return "recommendation: p2"  # Conditions met, resolve to "Yes"
    else:
        return "recommendation: p1"  # Points condition not met, resolve to "No"

if __name__ == "__main__":
    result = resolve_market()
    print(result)