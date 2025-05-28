import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Constants
GAME_DATE = "2025-05-27"
PLAYER_NAME = "Tyrese Haliburton"
TEAM_NAME = "Indiana Pacers"
OPPONENT_TEAM = "New York Knicks"
POINTS_THRESHOLD = 21.5

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Headers for API request
HEADERS = {
    "Ocp-Apim-Subscription-Key": API_KEY
}

def get_game_data(date, team):
    """
    Fetches game data for a specific date and team.
    """
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == team or game['AwayTeam'] == team:
                return game
    except requests.RequestException as e:
        logger.error(f"Error fetching game data: {e}")
        return None

def get_player_stats(game_id, player_name):
    """
    Fetches player stats for a specific game.
    """
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == player_name:
                return stat
    except requests.RequestException as e:
        logger.error(f"Error fetching player stats: {e}")
        return None

def resolve_market():
    """
    Resolves the market based on the player's performance.
    """
    game = get_game_data(GAME_DATE, TEAM_NAME)
    if not game:
        return "recommendation: p1"  # No game found, resolve to "No"

    if game['Status'] != "Final":
        return "recommendation: p1"  # Game not completed, resolve to "No"

    player_stats = get_player_stats(game['GameID'], PLAYER_NAME)
    if not player_stats:
        return "recommendation: p1"  # Player did not play, resolve to "No"

    points_scored = player_stats.get('Points', 0)
    if points_scored > POINTS_THRESHOLD:
        return "recommendation: p2"  # Yes, player scored more than 21.5 points
    else:
        return "recommendation: p1"  # No, player did not score more than 21.5 points

if __name__ == "__main__":
    result = resolve_market()
    print(result)