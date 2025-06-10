import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Game and player details
GAME_DATE = "2025-05-28"
PLAYER_NAME = "Shai Gilgeous-Alexander"
TEAM_ABBREVIATION = "OKC"  # Oklahoma City Thunder

def get(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def fetch_player_stats(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    stats = get(url, HEADERS)
    if stats:
        for stat in stats:
            if stat['Name'] == player_name:
                return stat
    return None

def find_game_id(date, team):
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
    games = get(url, HEADERS)
    if games:
        for game in games:
            if game['HomeTeam'] == team or game['AwayTeam'] == team:
                return game['GameID']
    return None

def resolve_market():
    game_id = find_game_id(GAME_DATE, TEAM_ABBREVIATION)
    if not game_id:
        print("Game not found or not scheduled.")
        return "recommendation: p1"  # Resolve to "No" if game not found

    player_stats = fetch_player_stats(game_id, PLAYER_NAME)
    if not player_stats:
        print("Player did not play or stats not available.")
        return "recommendation: p1"  # Resolve to "No" if player did not play

    points_scored = player_stats.get('Points', 0)
    if points_scored > 33.5:
        print(f"{PLAYER_NAME} scored {points_scored} points.")
        return "recommendation: p2"  # Resolve to "Yes"
    else:
        print(f"{PLAYER_NAME} scored {points_scored} points.")
        return "recommendation: p1"  # Resolve to "No"

if __name__ == "__main__":
    result = resolve_market()
    print(result)