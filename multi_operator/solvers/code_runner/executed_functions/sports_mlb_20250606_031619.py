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
            print("Proxy failed, trying primary endpoint...")
            return make_request(endpoint, path, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to check game outcome and player performance
def check_game_and_performance(date, team, player):
    # Format date for API request
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PRIMARY_ENDPOINT, f"/scores/json/GamesByDate/{formatted_date}", use_proxy=True)
    
    if not games_today:
        return "p1"  # Resolve to "No" if no data available

    # Find the specific game
    game_info = next((game for game in games_today if team in [game['HomeTeam'], game['AwayTeam']]), None)
    if not game_info:
        return "p1"  # Resolve to "No" if game not found

    # Check if game was postponed or cancelled
    if game_info['Status'] != 'Final':
        return "p1"  # Resolve to "No" if game not completed

    # Check player performance
    player_stats = make_request(PRIMARY_ENDPOINT, f"/stats/json/PlayerGameStatsByDate/{formatted_date}", use_proxy=True)
    player_game_stats = next((stat for stat in player_stats if stat['Name'] == player and stat['Team'] == team), None)
    
    if not player_game_stats:
        return "p1"  # Resolve to "No" if player did not play or no stats found

    # Check conditions for resolution
    pacers_win = (game_info['HomeTeam'] == team and game_info['HomeTeamScore'] > game_info['AwayTeamScore']) or \
                 (game_info['AwayTeam'] == team and game_info['AwayTeamScore'] > game_info['HomeTeamScore'])
    haliburton_score = player_game_stats['Points'] > 17.5

    if pacers_win and haliburton_score:
        return "p2"  # Resolve to "Yes"
    else:
        return "p1"  # Resolve to "No"

# Main execution
if __name__ == "__main__":
    game_date = "2025-06-05"
    team_name = "Indiana Pacers"
    player_name = "Tyrese Haliburton"
    recommendation = check_game_and_performance(game_date, team_name, player_name)
    print(f"recommendation: {recommendation}")