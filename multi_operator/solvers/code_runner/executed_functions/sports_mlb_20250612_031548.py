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

# Function to check game outcome and player performance
def check_game_and_performance(date, team, player_name, points_threshold):
    # Format date for API request
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PRIMARY_ENDPOINT, f"/scores/json/GamesByDate/{formatted_date}", use_proxy=True)
    
    if not games_today:
        return "p1"  # No data available, resolve as "No"

    # Find the specific game
    game = next((g for g in games_today if team in (g['HomeTeam'], g['AwayTeam'])), None)
    if not game:
        return "p1"  # Game not found, resolve as "No"

    # Check if game was postponed or cancelled
    if game['Status'] != 'Final':
        return "p1"  # Game not completed as scheduled, resolve as "No"

    # Check player performance
    player_stats = make_request(PRIMARY_ENDPOINT, f"/stats/json/PlayerGameStatsByDate/{formatted_date}", use_proxy=True)
    player_game_stats = next((p for p in player_stats if p['Name'] == player_name and p['GameId'] == game['GameId']), None)

    if not player_game_stats:
        return "p1"  # Player did not play or data missing, resolve as "No"

    # Check conditions for resolving as "Yes"
    pacers_win = (game['HomeTeam'] == team and game['HomeTeamScore'] > game['AwayTeamScore']) or \
                 (game['AwayTeam'] == team and game['AwayTeamScore'] > game['HomeTeamScore'])
    haliburton_scores_18_plus = player_game_stats['Points'] > points_threshold

    if pacers_win and haliburton_scores_18_plus:
        return "p2"  # Both conditions met, resolve as "Yes"
    else:
        return "p1"  # Conditions not met, resolve as "No"

# Main execution
if __name__ == "__main__":
    result = check_game_and_performance("2025-06-11", "Indiana Pacers", "Tyrese Haliburton", 17.5)
    print(f"recommendation: {result}")