import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Game and player details
GAME_DATE = "2025-06-12"
PLAYER_NAME = "Matthew Tkachuk"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution conditions
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scores more than 0.5 goals
    "No": "p1",   # Player scores 0.5 goals or less
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        # Fallback to proxy endpoint
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

def check_player_goals(game_data, player_name):
    for game in game_data:
        if game['Status'] == 'Final' and (game['HomeTeam'] in TEAM_ABBREVIATIONS.values() or game['AwayTeam'] in TEAM_ABBREVIATIONS.values()):
            for player in game['PlayerStats']:
                if player['Name'] == player_name and player['Goals'] > 0.5:
                    return "Yes"
    return "No"

def resolve_market():
    current_date = datetime.now().strftime("%Y-%m-%d")
    if current_date > "2025-12-31":
        return RESOLUTION_MAP["50-50"]
    elif current_date < GAME_DATE:
        return RESOLUTION_MAP["Too early to resolve"]

    game_data = get_game_data(GAME_DATE)
    if not game_data:
        return RESOLUTION_MAP["50-50"]

    result = check_player_goals(game_data, PLAYER_NAME)
    return RESOLUTION_MAP[result]

if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")