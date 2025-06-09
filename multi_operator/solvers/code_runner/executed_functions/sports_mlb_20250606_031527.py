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
DATE = "2025-06-05"
PLAYER_NAME = "Tyrese Haliburton"
TEAM = "Indiana Pacers"
OPPONENT = "Oklahoma City Thunder"
GAME_DATE = datetime.strptime(DATE, "%Y-%m-%d")

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find the game ID
def find_game_id(team, opponent, game_date):
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date.strftime('%Y-%m-%d')}"
    games = make_request(url, HEADERS)
    if games:
        for game in games:
            if (game['HomeTeam'] == team or game['AwayTeam'] == team) and \
               (game['HomeTeam'] == opponent or game['AwayTeam'] == opponent):
                return game['GameID']
    return None

# Function to check player's points
def check_player_points(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    stats = make_request(url, HEADERS)
    if stats:
        for stat in stats:
            if stat['Name'] == player_name:
                points = stat.get('Points', 0)
                return points >= 17.5
    return False

# Main function to resolve the market
def resolve_market():
    game_id = find_game_id(TEAM, OPPONENT, GAME_DATE)
    if game_id:
        if check_player_points(game_id, PLAYER_NAME):
            return "recommendation: p2"  # Yes, scored 18+ points
        else:
            return "recommendation: p1"  # No, did not score 18+ points
    return "recommendation: p1"  # No game found or player did not play

# Run the resolution
if __name__ == "__main__":
    print(resolve_market())