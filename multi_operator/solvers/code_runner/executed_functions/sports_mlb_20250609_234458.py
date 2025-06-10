import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Constants
DATE = "2025-05-29"
TEAM = "Indiana Pacers"
PLAYER = "Tyrese Haliburton"
POINTS_THRESHOLD = 22.5
GAME_ID = "547969"  # Example game ID, this would normally be fetched or predefined

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_game_data():
    # Construct URL for game data
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{DATE}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if TEAM in (game['HomeTeam'], game['AwayTeam']):
                return game
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
    return None

def get_player_stats(game_id, player_name):
    # Construct URL for player stats
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == player_name:
                return stat
    except requests.RequestException as e:
        print(f"Error fetching player stats: {e}")
    return None

def resolve_market():
    game = get_game_data()
    if not game:
        print("Game data not found or error occurred.")
        return "recommendation: p1"  # Resolve to "No" if game data is not available

    if game['Status'] != 'Final':
        print("Game is not completed.")
        return "recommendation: p1"  # Resolve to "No" if game is not completed

    player_stats = get_player_stats(game['GameID'], PLAYER)
    if not player_stats:
        print("Player stats not found or error occurred.")
        return "recommendation: p1"  # Resolve to "No" if player did not play or data is not available

    pacers_win = (game['HomeTeam'] == TEAM and game['HomeTeamScore'] > game['AwayTeamScore']) or \
                 (game['AwayTeam'] == TEAM and game['AwayTeamScore'] > game['HomeTeamScore'])
    haliburton_scores_23_plus = player_stats['Points'] > POINTS_THRESHOLD

    if pacers_win and haliburton_scores_23_plus:
        print("Both conditions met: Pacers win and Haliburton scores 23+ points.")
        return "recommendation: p2"  # Resolve to "Yes"
    else:
        print("Conditions not met.")
        return "recommendation: p1"  # Resolve to "No"

if __name__ == "__main__":
    result = resolve_market()
    print(result)