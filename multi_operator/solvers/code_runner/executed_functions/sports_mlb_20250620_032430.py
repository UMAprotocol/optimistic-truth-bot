import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
DATE = "2025-06-19"
PLAYER_NAME = "Jalen Williams"
TEAM = "Oklahoma City Thunder"
OPPONENT = "Indiana Pacers"
GAME_STATUS_FINAL = "Final"
POINTS_THRESHOLD = 24.5

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# URL for NBA data
NBA_SCORES_URL = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}"

def get_game_data(date):
    url = NBA_SCORES_URL.format(date=date)
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if game['Status'] == GAME_STATUS_FINAL and \
               (game['HomeTeam'] == TEAM or game['AwayTeam'] == TEAM) and \
               (game['HomeTeam'] == OPPONENT or game['AwayTeam'] == OPPONENT):
                return game
    return None

def get_player_stats(game_id, player_name):
    player_stats_url = f"https://api.sportsdata.io/v3/nba/stats/json/PlayerGameStatsByGame/{game_id}"
    response = requests.get(player_stats_url, headers=HEADERS)
    if response.status_code == 200:
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == player_name:
                return stat
    return None

def resolve_market():
    game_data = get_game_data(DATE)
    if not game_data:
        return "recommendation: p1"  # Game not found or not final, resolve to "No"

    player_stats = get_player_stats(game_data['GameID'], PLAYER_NAME)
    if not player_stats:
        return "recommendation: p1"  # Player did not play or stats not found, resolve to "No"

    points_scored = player_stats.get('Points', 0)
    if points_scored > POINTS_THRESHOLD:
        return "recommendation: p2"  # Yes, player scored more than 24.5 points
    else:
        return "recommendation: p1"  # No, player did not score more than 24.5 points

if __name__ == "__main__":
    print(resolve_market())