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
GAME_DATE = "2025-05-31"
PLAYER_NAME = "Tyrese Haliburton"
TEAM_NAME = "Indiana Pacers"
OPPONENT_TEAM = "New York Knicks"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Yes": "p2",  # Tyrese Haliburton scores 21+ points
    "No": "p1"    # Tyrese Haliburton scores 20.5 points or less
}

def get_game_data(date, team, opponent):
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team or game['AwayTeam'] == team) and \
               (game['HomeTeam'] == opponent or game['AwayTeam'] == opponent):
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error fetching game data: {e}")
    return None

def get_player_stats(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == player_name:
                return stat
    except requests.exceptions.RequestException as e:
        print(f"Error fetching player stats: {e}")
    return None

def resolve_market(game, player_stats):
    if not game or not player_stats:
        return "recommendation: " + RESOLUTION_MAP["No"]
    if game['Status'] != "Final" or player_stats['Played'] == 0:
        return "recommendation: " + RESOLUTION_MAP["No"]
    points = player_stats.get('Points', 0)
    if points > 20.5:
        return "recommendation: " + RESOLUTION_MAP["Yes"]
    else:
        return "recommendation: " + RESOLUTION_MAP["No"]

if __name__ == "__main__":
    game = get_game_data(GAME_DATE, TEAM_NAME, OPPONENT_TEAM)
    if game:
        player_stats = get_player_stats(game['GameID'], PLAYER_NAME)
        print(resolve_market(game, player_stats))
    else:
        print("recommendation: " + RESOLUTION_MAP["No"])