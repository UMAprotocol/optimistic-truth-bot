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
GAME_DATE = "2025-05-31"
TEAMS = ("Indiana Pacers", "New York Knicks")
PLAYER_NAME = "Tyrese Haliburton"
POINTS_THRESHOLD = 20.5

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
            print("Proxy failed, trying primary endpoint...")
            return make_request(url, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to find the game and check the outcome
def check_game_and_player_performance():
    # Format the date for the API request
    formatted_date = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(f"/scores/json/GamesByDate/{formatted_date}", use_proxy=True)

    if not games_today:
        return "p1"  # Resolve to "No" if no data is available

    # Find the specific game
    game = next((g for g in games_today if {g['HomeTeam'], g['AwayTeam']} == set(TEAMS)), None)
    if not game:
        return "p1"  # Resolve to "No" if the game is not found

    # Check if the game was postponed or cancelled
    if game['Status'] != 'Final':
        return "p1"  # Resolve to "No" if the game is not completed

    # Check the game outcome
    pacers_win = (game['HomeTeam'] == "IND" and game['HomeTeamScore'] > game['AwayTeamScore']) or \
                 (game['AwayTeam'] == "IND" and game['AwayTeamScore'] > game['HomeTeamScore'])

    # Check player performance
    player_stats = make_request(f"/stats/json/PlayerGameStatsByDate/{formatted_date}", use_proxy=True)
    if not player_stats:
        return "p1"  # Resolve to "No" if no player stats are available

    haliburton_stats = next((p for p in player_stats if p['Name'] == PLAYER_NAME and p['Team'] == "IND"), None)
    if not haliburton_stats:
        return "p1"  # Resolve to "No" if Haliburton did not play

    haliburton_scores_21_plus = haliburton_stats['Points'] > POINTS_THRESHOLD

    # Final resolution based on both conditions
    if pacers_win and haliburton_scores_21_plus:
        return "p2"  # Resolve to "Yes"
    else:
        return "p1"  # Resolve to "No"

# Main execution
if __name__ == "__main__":
    recommendation = check_game_and_player_performance()
    print(f"recommendation: {recommendation}")