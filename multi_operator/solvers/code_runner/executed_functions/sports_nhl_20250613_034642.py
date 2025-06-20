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
PLAYER_NAME = "Sam Bennett"
TEAMS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution conditions
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scores more than 0.5 goals
    "No": "p1",   # Player does not score more than 0.5 goals
    "50-50": "p3" # Game not completed by the deadline
}

def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def check_player_goals(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/scores/json/PlayerGameStatsByGame/{game_id}"
    data = get_data(url, HEADERS)
    if data:
        for player in data:
            if player["Name"] == player_name and player["Goals"] > 0.5:
                return "Yes"
    return "No"

def find_game_id(game_date, teams):
    date_str = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_str}"
    games = get_data(url, HEADERS)
    if games:
        for game in games:
            if game["HomeTeam"] in teams.values() and game["AwayTeam"] in teams.values():
                return game["GameID"]
    return None

def resolve_market():
    current_time = datetime.utcnow()
    deadline = datetime.strptime("2025-12-31 23:59", "%Y-%m-%d %H:%M")
    if current_time > deadline:
        return RESOLUTION_MAP["50-50"]

    game_id = find_game_id(GAME_DATE, TEAMS)
    if not game_id:
        return RESOLUTION_MAP["50-50"]

    result = check_player_goals(game_id, PLAYER_NAME)
    return RESOLUTION_MAP[result]

if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")