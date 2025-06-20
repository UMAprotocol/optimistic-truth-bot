import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}
GAME_DATE = "2025-06-17"
PLAYER_NAME = "Sam Bennett"
TEAMS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution map
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "50-50": "p3"
}

def get_game_data():
    date_str = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_str}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] in TEAMS.values() and game['AwayTeam'] in TEAMS.values():
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error accessing primary endpoint: {e}")
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{date_str}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if game['HomeTeam'] in TEAMS.values() and game['AwayTeam'] in TEAMS.values():
                    return game
        except requests.exceptions.RequestException as e:
            print(f"Error accessing proxy endpoint: {e}")
    return None

def check_player_goals(game_id):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == PLAYER_NAME and stat['Goals'] > 0.5:
                return "Yes"
    except requests.exceptions.RequestException as e:
        print(f"Error accessing primary endpoint for player stats: {e}")
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            player_stats = response.json()
            for stat in player_stats:
                if stat['Name'] == PLAYER_NAME and stat['Goals'] > 0.5:
                    return "Yes"
        except requests.exceptions.RequestException as e:
            print(f"Error accessing proxy endpoint for player stats: {e}")
    return "No"

def main():
    game = get_game_data()
    if not game:
        print("recommendation:", RESOLUTION_MAP["50-50"])
        return
    if datetime.now() < datetime.strptime(GAME_DATE + " 23:59:59", "%Y-%m-%d %H:%M:%S"):
        print("recommendation:", RESOLUTION_MAP["50-50"])
        return
    result = check_player_goals(game['GameID'])
    print("recommendation:", RESOLUTION_MAP[result])

if __name__ == "__main__":
    main()