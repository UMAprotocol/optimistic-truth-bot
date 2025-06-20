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
GAME_DATE = "2025-06-19"
PLAYER_NAME = "Jalen Williams"
TEAM_NAME = "Oklahoma City Thunder"
OPPONENT_TEAM = "Indiana Pacers"

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

# Resolution map
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "Unknown": "p3"
}

def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def find_game(games, team_name, opponent_team):
    for game in games:
        if (game['HomeTeam'] == team_name or game['AwayTeam'] == team_name) and \
           (game['HomeTeam'] == opponent_team or game['AwayTeam'] == opponent_team):
            return game
    return None

def check_player_performance(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    data = get_data(url, HEADERS)
    if data:
        for player in data:
            if player['Name'] == player_name:
                points = player.get('Points', 0)
                return points >= 25.5
    return False

def main():
    # Fetch games by date
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}"
    games = get_data(url, HEADERS)
    if not games:
        print("No games found or error in data retrieval.")
        return

    # Find specific game
    game = find_game(games, TEAM_NAME, OPPONENT_TEAM)
    if not game:
        print("Game not found.")
        return

    # Check if game was cancelled or postponed
    if game['Status'] != 'Final':
        print("recommendation:", RESOLUTION_MAP["No"])
        return

    # Check player performance
    game_id = game['GameID']
    if check_player_performance(game_id, PLAYER_NAME):
        print("recommendation:", RESOLUTION_MAP["Yes"])
    else:
        print("recommendation:", RESOLUTION_MAP["No"])

if __name__ == "__main__":
    main()