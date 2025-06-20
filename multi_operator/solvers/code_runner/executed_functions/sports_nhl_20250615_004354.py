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

# Resolution conditions
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
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
        if game['Status'] != 'Final':
            continue
        for player in game['PlayerStats']:
            if player['Name'] == player_name and player['Goals'] > 0.5:
                return "Yes"
    return "No"

def resolve_market():
    # Construct URL for the game date
    url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}"
    data = get_data(url, HEADERS)
    if not data:
        # Fallback to primary endpoint if proxy fails
        url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}"
        data = get_data(url, HEADERS)
        if not data:
            return "50-50"  # Unable to fetch data

    # Check if Brad Marchand scored more than 0.5 goals
    result = check_player_goals(data, PLAYER_NAME)
    return RESOLUTION_MAP[result]

if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")