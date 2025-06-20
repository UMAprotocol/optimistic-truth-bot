import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}
GAME_DATE = "2025-06-14"
PLAYER_NAME = "Evan Bouchard"
TEAMS = ["EDM", "FLA"]  # Edmonton Oilers and Florida Panthers

# API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Resolution map based on the ancillary data
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

def check_player_goals(game_id, player_name):
    url = f"{PROXY_ENDPOINT}/scores/json/PlayerGameStatsByGame/{game_id}"
    game_stats = get_data(url, HEADERS)
    if game_stats is None:
        url = f"{PRIMARY_ENDPOINT}/scores/json/PlayerGameStatsByGame/{game_id}"
        game_stats = get_data(url, HEADERS)
    if game_stats:
        for stat in game_stats:
            if stat["Name"] == player_name and stat["Goals"] > 0.5:
                return "Yes"
    return "No"

def find_game_id(game_date, teams):
    date_str = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{date_str}"
    games = get_data(url, HEADERS)
    if games is None:
        url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_str}"
        games = get_data(url, HEADERS)
    if games:
        for game in games:
            if game["HomeTeam"] in teams and game["AwayTeam"] in teams:
                return game["GameID"]
    return None

def main():
    game_id = find_game_id(GAME_DATE, TEAMS)
    if game_id:
        result = check_player_goals(game_id, PLAYER_NAME)
        recommendation = RESOLUTION_MAP.get(result, "p3")  # Default to 50-50 if no clear result
    else:
        recommendation = "p3"  # 50-50 if game not found or not completed
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()