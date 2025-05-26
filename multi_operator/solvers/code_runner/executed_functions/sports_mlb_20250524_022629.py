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

# Function to make API requests
def make_request(endpoint, path, use_proxy=False):
    url = f"{PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(endpoint, path, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to check Jalen Brunson's score
def check_jalen_brunson_score():
    date_of_game = "2025-05-23"
    player_name = "Jalen Brunson"
    team_id = "New York Knicks"  # This would ideally be fetched or predefined

    # Fetch games by date
    games = make_request(PRIMARY_ENDPOINT, f"/scores/json/GamesByDate/{date_of_game}", use_proxy=True)
    if not games:
        return "p1"  # No games found or API failure, resolve as "No" per conditions

    # Find the specific game
    game = next((g for g in games if g['HomeTeam'] == team_id or g['AwayTeam'] == team_id), None)
    if not game:
        return "p1"  # Game not found, resolve as "No"

    # Check if the game was postponed or cancelled
    if game['Status'] != 'Final':
        return "p1"  # Game not completed as scheduled, resolve as "No"

    # Fetch player stats for the game
    game_id = game['GameID']
    player_stats = make_request(PRIMARY_ENDPOINT, f"/stats/json/PlayerGameStatsByGame/{game_id}", use_proxy=True)
    if not player_stats:
        return "p1"  # No player stats found, resolve as "No"

    # Find Jalen Brunson's stats
    brunson_stats = next((p for p in player_stats if p['Name'] == player_name), None)
    if not brunson_stats:
        return "p1"  # Brunson did not play, resolve as "No"

    # Check if Brunson scored 30 or more points
    if brunson_stats['Points'] > 29.5:
        return "p2"  # Yes, he scored 30+ points
    else:
        return "p1"  # No, he did not score 30+ points

# Main execution
if __name__ == "__main__":
    recommendation = check_jalen_brunson_score()
    print(f"recommendation: {recommendation}")