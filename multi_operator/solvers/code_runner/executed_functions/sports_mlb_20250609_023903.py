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
def make_request(endpoint, path):
    url = f"{endpoint}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if endpoint == PROXY_ENDPOINT:
            print("Proxy failed, trying primary endpoint")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"Error: {e}")
            return None

# Function to check the game result and player performance
def check_game_and_performance():
    date_str = "2025-06-08"
    team = "Indiana Pacers"
    opponent = "Oklahoma City Thunder"
    player = "Tyrese Haliburton"
    required_points = 17

    # Fetch games by date
    games = make_request(PROXY_ENDPOINT, f"/scores/json/GamesByDate/{date_str}")
    if not games:
        return "p1"  # Resolve to "No" if no data available

    # Find the specific game
    game = next((g for g in games if team in g['HomeTeam'] or team in g['AwayTeam']), None)
    if not game:
        return "p1"  # Resolve to "No" if game not found

    # Check if game was postponed or cancelled
    if game['Status'] != 'Final':
        return "p1"  # Resolve to "No" if game not completed

    # Check game outcome
    pacers_win = (game['HomeTeam'] == team and game['HomeTeamScore'] > game['AwayTeamScore']) or \
                 (game['AwayTeam'] == team and game['AwayTeamScore'] > game['HomeTeamScore'])

    # Fetch player stats
    player_stats = make_request(PROXY_ENDPOINT, f"/stats/json/PlayerGameStatsByDate/{date_str}")
    if not player_stats:
        return "p1"  # Resolve to "No" if no player stats available

    # Find player performance
    haliburton_performance = next((p for p in player_stats if p['Name'] == player and p['Team'] == team), None)
    if not haliburton_performance:
        return "p1"  # Resolve to "No" if player did not play

    # Check points scored
    haliburton_points = haliburton_performance['Points'] >= required_points

    # Final resolution based on conditions
    if pacers_win and haliburton_points:
        return "p2"  # Resolve to "Yes"
    else:
        return "p1"  # Resolve to "No"

# Main execution
if __name__ == "__main__":
    recommendation = check_game_and_performance()
    print(f"recommendation: {recommendation}")