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
        print(f"Error: {e}")
        return None

# Function to check game results and player scores
def check_game_and_scores():
    date_str = "2025-05-23"
    team = "Indiana Pacers"
    opponent = "New York Knicks"
    player = "Tyrese Haliburton"
    score_threshold = 20.5

    # Fetch games by date
    games_today = make_request(PRIMARY_ENDPOINT, f"/scores/json/GamesByDate/{date_str}")
    if not games_today:
        return "p1"  # Resolve to "No" if API fails or no data

    # Find the specific game
    game_info = next((game for game in games_today if team in game['HomeTeam'] or team in game['AwayTeam']), None)
    if not game_info:
        return "p1"  # No game found

    # Check if the game was postponed or cancelled
    if game_info['Status'] != 'Final':
        return "p1"  # Game not completed as required

    # Check game outcome
    pacers_win = (game_info['HomeTeam'] == team and game_info['HomeTeamScore'] > game_info['AwayTeamScore']) or \
                 (game_info['AwayTeam'] == team and game_info['AwayTeamScore'] > game_info['HomeTeamScore'])

    # Fetch player stats
    game_id = game_info['GameID']
    player_stats = make_request(PRIMARY_ENDPOINT, f"/stats/json/PlayerGameStatsByGame/{game_id}")
    if not player_stats:
        return "p1"  # Resolve to "No" if API fails or no data

    # Find Haliburton's stats
    haliburton_stats = next((stat for stat in player_stats if stat['Name'] == player and stat['Team'] == team), None)
    if not haliburton_stats:
        return "p1"  # Haliburton did not play or no stats

    # Check Haliburton's score
    haliburton_scored_21_plus = haliburton_stats['Points'] > score_threshold

    # Final resolution based on conditions
    if pacers_win and haliburton_scored_21_plus:
        return "p2"  # Yes
    else:
        return "p1"  # No

# Main execution
if __name__ == "__main__":
    recommendation = check_game_and_scores()
    print(f"recommendation: {recommendation}")