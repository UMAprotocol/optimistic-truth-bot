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
    # Fetch games by date
    games = make_request(f"/scores/json/GamesByDate/{GAME_DATE}", use_proxy=True)
    if not games:
        return "p4"  # Unable to retrieve data

    # Find the specific game
    game = next((g for g in games if TEAM_NAME in (g['HomeTeam'], g['AwayTeam'])), None)
    if not game:
        return "p1"  # Game not found or not scheduled

    # Check if game was postponed or cancelled
    if game['Status'] != 'Final':
        return "p1"  # Game not completed as scheduled

    # Check player performance if game was completed
    player_stats = make_request(f"/stats/json/PlayerGameStatsByDate/{GAME_DATE}", use_proxy=True)
    if not player_stats:
        return "p4"  # Unable to retrieve player stats

    # Find the player and check points
    player_stat = next((p for p in player_stats if p['Name'] == PLAYER_NAME and p['Team'] == game['HomeTeam'] or p['Team'] == game['AwayTeam']), None)
    if not player_stat:
        return "p1"  # Player did not play

    points_scored = player_stat.get('Points', 0)
    knicks_won = (game['HomeTeam'] == TEAM_NAME and game['HomeTeamScore'] > game['AwayTeamScore']) or \
                 (game['AwayTeam'] == TEAM_NAME and game['AwayTeamScore'] > game['HomeTeamScore'])

    # Check both conditions: Knicks win and Brunson scores over 30.5 points
    if knicks_won and points_scored > POINTS_THRESHOLD:
        return "p2"  # Both conditions met
    else:
        return "p1"  # Conditions not met

# Main execution
if __name__ == "__main__":
    result = check_game_and_player_performance()
    print(f"recommendation: {result}")