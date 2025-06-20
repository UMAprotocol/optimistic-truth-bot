import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Game and player details
GAME_DATE = "2025-06-14"
PLAYER_NAME = "Brad Marchand"
TEAMS = ["EDM", "FLA"]  # Edmonton Oilers and Florida Panthers

# Resolution map based on the outcome
RESOLUTION_MAP = {
    "YES": "p2",  # Player scored more than 0.5 goals
    "NO": "p1",   # Player did not score more than 0.5 goals
    "UNKNOWN": "p3"  # Game not completed or data unavailable
}

def get_game_data(date, teams):
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] in teams and game['AwayTeam'] in teams:
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error fetching game data: {e}")
    return None

def check_player_goals(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == player_name:
                goals = stat.get('Goals', 0)
                return "YES" if goals > 0.5 else "NO"
    except requests.exceptions.RequestException as e:
        print(f"Error fetching player stats: {e}")
    return "UNKNOWN"

def main():
    game = get_game_data(GAME_DATE, TEAMS)
    if not game:
        print("recommendation:", RESOLUTION_MAP["UNKNOWN"])
        return
    if game['Status'] != "Final":
        print("recommendation:", RESOLUTION_MAP["UNKNOWN"])
        return
    result = check_player_goals(game['GameID'], PLAYER_NAME)
    print("recommendation:", RESOLUTION_MAP[result])

if __name__ == "__main__":
    main()