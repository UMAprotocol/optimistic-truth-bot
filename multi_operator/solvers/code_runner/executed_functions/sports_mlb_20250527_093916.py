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
def make_request(endpoint, path, use_proxy=True):
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
            print(f"Failed to retrieve data from {url}: {e}")
            return None

# Function to check game results and player scores
def check_game_and_scores():
    date_str = "2025-05-26"
    team = "Minnesota Timberwolves"
    opponent = "Oklahoma City Thunder"
    player = "Anthony Edwards"
    score_threshold = 30.5

    # Fetch games by date
    games_today = make_request(PRIMARY_ENDPOINT, f"/scores/json/GamesByDate/{date_str}")
    if not games_today:
        return "p1"  # Resolve to "No" if no data available

    # Find the specific game
    game = next((g for g in games_today if team in g['HomeTeam'] or team in g['AwayTeam']), None)
    if not game:
        return "p1"  # Resolve to "No" if game not found

    # Check if game was postponed or cancelled
    if game['Status'] != 'Final':
        return "p1"  # Resolve to "No" if game not completed

    # Check game outcome
    timberwolves_win = (game['HomeTeam'] == team and game['HomeTeamScore'] > game['AwayTeamScore']) or \
                       (game['AwayTeam'] == team and game['AwayTeamScore'] > game['HomeTeamScore'])

    # Fetch player stats
    game_id = game['GameID']
    player_stats = make_request(PRIMARY_ENDPOINT, f"/stats/json/PlayerGameStatsByGame/{game_id}")
    if not player_stats:
        return "p1"  # Resolve to "No" if no player stats available

    # Find Anthony Edwards' stats
    edwards_stats = next((p for p in player_stats if p['Name'] == player and p['Team'] == team), None)
    if not edwards_stats:
        return "p1"  # Resolve to "No" if player stats not found

    # Check if Edwards scored more than 30.5 points
    edwards_scored_enough = edwards_stats['Points'] > score_threshold

    # Final resolution based on game outcome and player performance
    if timberwolves_win and edwards_scored_enough:
        return "p2"  # Resolve to "Yes"
    else:
        return "p1"  # Resolve to "No"

# Main execution
if __name__ == "__main__":
    recommendation = check_game_and_scores()
    print(f"recommendation: {recommendation}")