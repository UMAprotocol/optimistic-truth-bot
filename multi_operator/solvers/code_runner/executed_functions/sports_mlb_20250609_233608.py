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
GAME_DATE = "2025-05-29"
TEAM_NAME = "New York Knicks"
PLAYER_NAME = "Jalen Brunson"
POINTS_THRESHOLD = 30.5

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
    games_url = f"/scores/json/GamesByDate/{GAME_DATE}"
    games_data = make_request(games_url)
    if games_data is None:
        return "p1"  # Resolve to "No" if data retrieval fails

    # Find the specific game
    game = next((g for g in games_data if TEAM_NAME in (g['HomeTeam'], g['AwayTeam'])), None)
    if not game:
        return "p1"  # No game found, resolve to "No"

    # Check if game was cancelled or postponed
    if game['Status'] != 'Final':
        return "p1"  # Game not completed normally, resolve to "No"

    # Check player performance
    player_stats_url = f"/stats/json/PlayerGameStatsByDate/{GAME_DATE}"
    player_stats_data = make_request(player_stats_url)
    if player_stats_data is None:
        return "p1"  # Resolve to "No" if data retrieval fails

    # Find player stats in the game
    player_stats = next((p for p in player_stats_data if p['Name'] == PLAYER_NAME and p['Team'] == game['HomeTeam'] or p['Team'] == game['AwayTeam']), None)
    if not player_stats or player_stats['Points'] <= POINTS_THRESHOLD:
        return "p1"  # Player did not score enough points or did not play, resolve to "No"

    # Check if the Knicks won
    knicks_won = (game['HomeTeam'] == TEAM_NAME and game['HomeTeamScore'] > game['AwayTeamScore']) or \
                 (game['AwayTeam'] == TEAM_NAME and game['AwayTeamScore'] > game['HomeTeamScore'])

    if knicks_won:
        return "p2"  # Knicks won and Brunson scored over 30.5 points
    else:
        return "p1"  # Knicks did not win

# Main execution
if __name__ == "__main__":
    result = check_game_and_player_performance()
    print(f"recommendation: {result}")