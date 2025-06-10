import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Constants
DATE = "2025-05-28"
TEAM = "Minnesota Timberwolves"
OPPONENT = "Oklahoma City Thunder"
PLAYER = "Anthony Edwards"
POINTS_THRESHOLD = 27.5

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def check_game_and_performance():
    # Construct URL to fetch games by date
    games_url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{DATE}"
    games_data = get_data(games_url)
    if not games_data:
        return "p1"  # Resolve to "No" if data cannot be fetched

    # Find the specific game
    game = next((g for g in games_data if TEAM in g['HomeTeam'] or TEAM in g['AwayTeam']), None)
    if not game:
        return "p1"  # No game found, resolve to "No"

    # Check if game was postponed or cancelled
    if game['Status'] != 'Final':
        return "p1"  # Game not completed normally, resolve to "No"

    # Check game outcome
    timberwolves_win = (game['HomeTeam'] == TEAM and game['HomeTeamScore'] > game['AwayTeamScore']) or \
                       (game['AwayTeam'] == TEAM and game['AwayTeamScore'] > game['HomeTeamScore'])

    # Fetch player stats
    player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByDate/{DATE}"
    player_stats_data = get_data(player_stats_url)
    if not player_stats_data:
        return "p1"  # Resolve to "No" if data cannot be fetched

    # Find Anthony Edwards' performance
    edwards_performance = next((p for p in player_stats_data if p['Name'] == PLAYER and p['Team'] == TEAM), None)
    if not edwards_performance:
        return "p1"  # Player did not play, resolve to "No"

    # Check points scored by Anthony Edwards
    edwards_scores_28_plus = edwards_performance['Points'] > POINTS_THRESHOLD

    # Final resolution based on conditions
    if timberwolves_win and edwards_scores_28_plus:
        return "p2"  # Resolve to "Yes"
    else:
        return "p1"  # Resolve to "No"

# Main execution
if __name__ == "__main__":
    recommendation = check_game_and_performance()
    print(f"recommendation: {recommendation}")