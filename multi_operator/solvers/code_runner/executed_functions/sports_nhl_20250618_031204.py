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
GAME_DATE = "2025-06-17"
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
            if set([game['HomeTeam'], game['AwayTeam']]) == set(TEAMS):
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        # Fallback to proxy endpoint
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if set([game['HomeTeam'], game['AwayTeam']]) == set(TEAMS):
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
                return stat['Goals'] > 0.5
    except requests.exceptions.RequestException as e:
        print(f"Error fetching player stats: {e}")
    return False

def resolve_market():
    current_date = datetime.utcnow().date()
    if current_date > datetime.strptime(GAME_DATE, "%Y-%m-%d").date():
        game = get_game_data(GAME_DATE)
        if game:
            if game['Status'] == 'Final':
                if check_player_goals(game['GameID'], PLAYER_NAME):
                    return RESOLUTION_MAP["Yes"]
                else:
                    return RESOLUTION_MAP["No"]
            elif game['Status'] in ['Canceled', 'Postponed']:
                return RESOLUTION_MAP["50-50"]
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["50-50"]

if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")