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
TEAM = "Oklahoma City Thunder"
OPPONENT_TEAM = "Minnesota Timberwolves"

# Function to make API requests
def make_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(url, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to find the game ID
def find_game_id():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%b-%d")
    games = make_request(f"/scores/json/GamesByDate/{date_formatted}", use_proxy=True)
    if games:
        for game in games:
            if game['HomeTeam'] == TEAM or game['AwayTeam'] == TEAM:
                if game['HomeTeam'] == OPPONENT_TEAM or game['AwayTeam'] == OPPONENT_TEAM:
                    return game['GameId']
    return None

# Function to check player's points
def check_player_points(game_id):
    game_boxscore = make_request(f"/stats/json/BoxScore/{game_id}", use_proxy=True)
    if game_boxscore:
        for player_game in game_boxscore['PlayerGames']:
            if player_game['Name'] == PLAYER_NAME:
                points = player_game['Points']
                return points >= 34
    return False

# Main function to resolve the market
def resolve_market():
    game_id = find_game_id()
    if game_id:
        if check_player_points(game_id):
            return "recommendation: p2"  # Yes, scored 34+ points
        else:
            return "recommendation: p1"  # No, did not score 34+ points
    return "recommendation: p1"  # No game found or player did not play

# Run the resolution process
if __name__ == "__main__":
    result = resolve_market()
    print(result)