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
GAME_DATE = "2025-06-17"
PLAYER_NAME = "Angel Reese"
TEAM_A = "Chicago Sky"
TEAM_B = "Washington Mystics"

# Function to make API requests
def make_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(url, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to find the game ID
def find_game_id():
    games_url = f"/scores/json/GamesByDate/{GAME_DATE}"
    games = make_request(games_url)
    if games:
        for game in games:
            if (game['HomeTeam'] == TEAM_A or game['AwayTeam'] == TEAM_A) and \
               (game['HomeTeam'] == TEAM_B or game['AwayTeam'] == TEAM_B):
                return game['GameID']
    return None

# Function to check player stats
def check_player_rebounds(game_id):
    boxscore_url = f"/stats/json/PlayerGameStatsByGame/{game_id}"
    stats = make_request(boxscore_url)
    if stats:
        for stat in stats:
            if stat['Name'] == PLAYER_NAME:
                rebounds = stat.get('Rebounds', 0)
                return rebounds >= 11
    return False

# Main function to resolve the market
def resolve_market():
    game_id = find_game_id()
    if game_id:
        if check_player_rebounds(game_id):
            return "recommendation: p2"  # Yes, more than 10.5 rebounds
        else:
            return "recommendation: p1"  # No, not more than 10.5 rebounds
    return "recommendation: p1"  # Default to No if game ID not found or other issues

# Run the main function
if __name__ == "__main__":
    result = resolve_market()
    print(result)