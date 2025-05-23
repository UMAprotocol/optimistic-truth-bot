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

# Function to check game outcome and player performance
def check_game_and_performance(date, team, player, points_threshold):
    games_today = make_request(PRIMARY_ENDPOINT, f"/scores/json/GamesByDate/{date}")
    if not games_today:
        return "p1"  # Resolve to "No" if no data available

    for game in games_today:
        if team in (game['HomeTeam'], game['AwayTeam']):
            if datetime.strptime(game['DateTime'], "%Y-%m-%dT%H:%M:%S") > datetime(2025, 5, 22, 23, 59):
                return "p1"  # Game postponed beyond the allowed time

            game_id = game['GameID']
            stats = make_request(PRIMARY_ENDPOINT, f"/stats/json/PlayerGameStatsByGame/{game_id}")
            if not stats:
                return "p1"  # Resolve to "No" if no stats available

            team_won = (game['Status'] == 'Final' and 
                        ((game['HomeTeam'] == team and game['HomeTeamScore'] > game['AwayTeamScore']) or
                         (game['AwayTeam'] == team and game['AwayTeamScore'] > game['HomeTeamScore'])))

            player_scored_enough = any(s['Name'] == player and s['Points'] > points_threshold for s in stats)

            if team_won and player_scored_enough:
                return "p2"  # Resolve to "Yes"
            else:
                return "p1"  # Resolve to "No"

    return "p1"  # Resolve to "No" if no matching game found

# Main execution function
if __name__ == "__main__":
    result = check_game_and_performance("2025-05-22", "OKL", "Shai Gilgeous-Alexander", 30.5)
    print(f"recommendation: {result}")