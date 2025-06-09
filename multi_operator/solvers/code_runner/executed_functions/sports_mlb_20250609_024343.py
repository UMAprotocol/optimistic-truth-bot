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
            print(f"Failed to retrieve data: {e}")
            return None

# Function to check game outcome and player performance
def check_game_and_performance():
    date_str = "2025-06-08"
    team = "Oklahoma City Thunder"
    player = "Shai Gilgeous-Alexander"
    required_points = 34

    # Fetch games by date
    games_today = make_request(PROXY_ENDPOINT, f"/scores/json/GamesByDate/{date_str}")
    if not games_today:
        return "recommendation: p1"  # Resolve to "No" if no data available

    # Find the specific game
    game = next((g for g in games_today if team in (g['HomeTeam'], g['AwayTeam'])), None)
    if not game or game['Status'] != 'Final':
        return "recommendation: p1"  # Game not completed or not found

    # Check if the game was postponed or cancelled
    if game['Status'] in ['Postponed', 'Canceled']:
        return "recommendation: p1"

    # Check game outcome
    thunder_won = (game['HomeTeam'] == team and game['HomeTeamScore'] > game['AwayTeamScore']) or \
                  (game['AwayTeam'] == team and game['AwayTeamScore'] > game['HomeTeamScore'])

    # Fetch player stats
    game_id = game['GameID']
    player_stats = make_request(PROXY_ENDPOINT, f"/stats/json/PlayerGameStatsByGame/{game_id}")
    if not player_stats:
        return "recommendation: p1"  # Resolve to "No" if no player data available

    # Find player performance
    player_performance = next((p for p in player_stats if p['Name'] == player), None)
    if not player_performance or player_performance['Points'] < required_points:
        return "recommendation: p1"

    # Final resolution based on conditions
    if thunder_won and player_performance['Points'] >= required_points:
        return "recommendation: p2"  # Yes
    else:
        return "recommendation: p1"  # No

# Main execution
if __name__ == "__main__":
    result = check_game_and_performance()
    print(result)