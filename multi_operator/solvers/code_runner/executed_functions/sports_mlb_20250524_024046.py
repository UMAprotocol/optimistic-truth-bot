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
            print(f"Falling back to primary endpoint due to error: {e}")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"Error accessing API: {e}")
            return None

# Function to check game outcome and player performance
def check_game_and_performance(date, team, player):
    # Format date for API request
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PROXY_ENDPOINT, f"/scores/json/GamesByDate/{formatted_date}")

    if not games_today:
        return "p1"  # No data available, resolve as "No"

    # Find the specific game
    for game in games_today:
        if team in (game['HomeTeam'], game['AwayTeam']):
            if game['Status'] != "Final":
                return "p1"  # Game not completed or postponed, resolve as "No"
            # Check game outcome
            team_won = (game['HomeTeam'] == team and game['HomeTeamScore'] > game['AwayTeamScore']) or \
                       (game['AwayTeam'] == team and game['AwayTeamScore'] > game['HomeTeamScore'])

            # Check player performance
            player_stats = make_request(PROXY_ENDPOINT, f"/stats/json/PlayerGameStatsByDate/{formatted_date}/{player}")
            if player_stats:
                for stat in player_stats:
                    if stat['Name'] == player and stat['Points'] > 29.5:
                        if team_won:
                            return "p2"  # Team won and player scored 30+ points, resolve as "Yes"
            return "p1"  # Either player did not score 30+ points or team did not win
    return "p1"  # Game not found or other conditions not met

# Main execution function
if __name__ == "__main__":
    # Specific game and player details
    game_date = "2025-05-23"
    team_name = "Knicks"
    player_name = "Jalen Brunson"

    # Get the recommendation based on the game and player performance
    recommendation = check_game_and_performance(game_date, team_name, player_name)
    print(f"recommendation: {recommendation}")