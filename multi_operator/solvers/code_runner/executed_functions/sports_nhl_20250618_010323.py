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
GAME_DATE = "2025-06-17"
PLAYER_NAME = "Matthew Tkachuk"
TEAMS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution conditions
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "50-50": "p3"
}

def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def check_player_goals(data, player_name):
    for game in data:
        for player in game.get('PlayerGames', []):
            if player.get('Name') == player_name and player.get('Goals', 0) > 0.5:
                return True
    return False

def resolve_market():
    # Construct URL for the game date
    url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}"
    data = get_data(url, HEADERS)
    if not data:
        # Fallback to primary endpoint if proxy fails
        url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}"
        data = get_data(url, HEADERS)
        if not data:
            return "recommendation: " + RESOLUTION_MAP["50-50"]

    # Check if the player scored more than 0.5 goals
    if check_player_goals(data, PLAYER_NAME):
        return "recommendation: " + RESOLUTION_MAP["Yes"]
    else:
        return "recommendation: " + RESOLUTION_MAP["No"]

if __name__ == "__main__":
    result = resolve_market()
    print(result)