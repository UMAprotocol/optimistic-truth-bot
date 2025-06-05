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

# Game and player specifics
GAME_DATE = "2025-05-31"
TEAM_NAME = "New York Knicks"
PLAYER_NAME = "Jalen Brunson"
SCORE_THRESHOLD = 31.5

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

# Function to find the game and check the conditions
def check_game_and_player_performance():
    # Fetch games by date
    games = make_request(f"/scores/json/GamesByDate/{GAME_DATE}")
    if not games:
        return "p1"  # Resolve to "No" if no data available

    # Find the specific game
    game = next((g for g in games if TEAM_NAME in (g['HomeTeam'], g['AwayTeam'])), None)
    if not game:
        return "p1"  # Resolve to "No" if game not found

    # Check if game was postponed or cancelled
    if game['Status'] not in ['Final', 'InProgress']:
        return "p1"  # Resolve to "No"

    # Check game outcome and player performance
    if game['Winner'] == TEAM_NAME:
        # Fetch player stats
        player_stats = make_request(f"/stats/json/PlayerGameStatsByDate/{GAME_DATE}")
        if player_stats:
            player_game = next((p for p in player_stats if p['Name'] == PLAYER_NAME and p['Team'] == TEAM_NAME), None)
            if player_game and player_game['Points'] > SCORE_THRESHOLD:
                return "p2"  # Resolve to "Yes"
    return "p1"  # Resolve to "No"

# Main execution
if __name__ == "__main__":
    result = check_game_and_player_performance()
    print(f"recommendation: {result}")