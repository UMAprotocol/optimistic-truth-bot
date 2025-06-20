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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Game and player details
GAME_DATE = "2025-06-14"
PLAYER_NAME = "Sam Bennett"
TEAMS = ["EDM", "FLA"]  # Edmonton Oilers and Florida Panthers

# Resolution conditions
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "50-50": "p3"
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] in TEAMS and game['AwayTeam'] in TEAMS:
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if game['HomeTeam'] in TEAMS and game['AwayTeam'] in TEAMS:
                    return game
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
    return None

def check_player_goals(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/PlayerGameStatsByGame/{game_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == player_name:
                goals = stat['Goals']
                return goals > 0.5
    except requests.exceptions.RequestException as e:
        print(f"Error fetching player stats: {e}")
    return False

def resolve_market():
    game = get_game_data(GAME_DATE)
    if not game:
        print("Game data not found or game not yet played.")
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    
    if datetime.now() < datetime.strptime(GAME_DATE + " 23:59", "%Y-%m-%d %H:%M"):
        print("Game has not been completed by the specified date.")
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    
    if game['Status'] != 'Final':
        print("Game is not in a final state.")
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    
    if check_player_goals(game['GameID'], PLAYER_NAME):
        return "recommendation: " + RESOLUTION_MAP["Yes"]
    else:
        return "recommendation: " + RESOLUTION_MAP["No"]

if __name__ == "__main__":
    result = resolve_market()
    print(result)