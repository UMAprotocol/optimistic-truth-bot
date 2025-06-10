import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

# Game and player details
GAME_DATE = "2025-05-28"
TEAM = "Oklahoma City Thunder"
PLAYER = "Shai Gilgeous-Alexander"
POINTS_THRESHOLD = 33.5

# Resolution map
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1"
}

def get_game_data():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%b-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_formatted}"
    proxy_url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{date_formatted}"

    try:
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Proxy failed")
    except:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            return None

    games = response.json()
    for game in games:
        if TEAM in [game["HomeTeam"], game["AwayTeam"]]:
            return game
    return None

def get_player_stats(game_id):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    proxy_url = f"{PROXY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"

    try:
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Proxy failed")
    except:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            return None

    stats = response.json()
    for stat in stats:
        if stat["Name"] == PLAYER:
            return stat
    return None

def resolve_market():
    game = get_game_data()
    if not game or game["Status"] != "Final":
        return RESOLUTION_MAP["No"]

    player_stats = get_player_stats(game["GameID"])
    if not player_stats or player_stats["Points"] <= POINTS_THRESHOLD:
        return RESOLUTION_MAP["No"]

    winning_team = game["HomeTeam"] if game["HomeTeamRuns"] > game["AwayTeamRuns"] else game["AwayTeam"]
    if winning_team == TEAM and player_stats["Points"] > POINTS_THRESHOLD:
        return RESOLUTION_MAP["Yes"]
    else:
        return RESOLUTION_MAP["No"]

if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")