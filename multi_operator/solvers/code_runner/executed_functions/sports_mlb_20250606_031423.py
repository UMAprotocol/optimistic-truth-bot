import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Game and player details
GAME_DATE = "2025-06-05"
PLAYER_NAME = "Tyrese Haliburton"
TEAM_ABBREVIATION = "IND"  # Indiana Pacers

# Resolution conditions
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "Unknown": "p3"
}

def get_game_id():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{date_formatted}"
    fallback_url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_formatted}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            response = requests.get(fallback_url, headers=HEADERS, timeout=10)
        games = response.json()
        for game in games:
            if game['HomeTeam'] == TEAM_ABBREVIATION or game['AwayTeam'] == TEAM_ABBREVIATION:
                return game['GameID']
    except Exception as e:
        print(f"Error fetching game ID: {e}")
    return None

def check_player_performance(game_id):
    url = f"{PROXY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    fallback_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            response = requests.get(fallback_url, headers=HEADERS, timeout=10)
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == PLAYER_NAME:
                points = stat['Points']
                return points >= 17.5
    except Exception as e:
        print(f"Error checking player performance: {e}")
    return False

def resolve_market():
    game_id = get_game_id()
    if not game_id:
        return RESOLUTION_MAP["No"]  # Game not found or error, resolve as "No"

    if check_player_performance(game_id):
        return RESOLUTION_MAP["Yes"]
    else:
        return RESOLUTION_MAP["No"]

if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")