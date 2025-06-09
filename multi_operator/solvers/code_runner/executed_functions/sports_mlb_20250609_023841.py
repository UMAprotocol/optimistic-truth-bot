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
def check_game_and_performance(date, team, player):
    # Format date for API request
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PROXY_ENDPOINT, f"/scores/json/GamesByDate/{formatted_date}")

    if not games_today:
        return "recommendation: p1"  # Resolve to "No" if data retrieval fails

    # Find the specific game
    for game in games_today:
        if game['HomeTeam'] == team or game['AwayTeam'] == team:
            if game['Status'] != "Final":
                return "recommendation: p1"  # Game not completed or postponed

            # Check if specified team won
            team_won = (game['HomeTeam'] == team and game['HomeTeamScore'] > game['AwayTeamScore']) or \
                       (game['AwayTeam'] == team and game['AwayTeamScore'] > game['HomeTeamScore'])

            # Check player performance
            player_stats = make_request(PROXY_ENDPOINT, f"/stats/json/PlayerGameStatsByDate/{formatted_date}/{player}")
            if not player_stats:
                return "recommendation: p1"  # Resolve to "No" if player stats are missing

            # Find player in the stats
            for stat in player_stats:
                if stat['Name'] == player and stat['Points'] > 16.5:
                    if team_won:
                        return "recommendation: p2"  # Both conditions met
                    break

    return "recommendation: p1"  # Default to "No" if conditions are not met

# Main execution function
if __name__ == "__main__":
    game_date = "2025-06-08"
    team = "Indiana Pacers"
    player = "Tyrese Haliburton"
    print(check_game_and_performance(game_date, team, player))