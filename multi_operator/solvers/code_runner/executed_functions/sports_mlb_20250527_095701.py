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
            print("Proxy failed, trying primary endpoint.")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to check game outcome and player performance
def check_game_and_performance(date, team, player_name, points_threshold):
    # Format date for API request
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PROXY_ENDPOINT, f"/scores/json/GamesByDate/{formatted_date}")

    if not games_today:
        return "p1"  # Resolve to "No" if no data available

    for game in games_today:
        if team in [game['HomeTeam'], game['AwayTeam']] and game['Status'] == "Final":
            # Check if the team won
            team_won = (game['HomeTeam'] == team and game['HomeTeamScore'] > game['AwayTeamScore']) or \
                       (game['AwayTeam'] == team and game['AwayTeamScore'] > game['HomeTeamScore'])

            # Check player performance
            player_stats = make_request(PROXY_ENDPOINT, f"/stats/json/PlayerGameStatsByDate/{formatted_date}")
            if player_stats:
                for player in player_stats:
                    if player['Name'] == player_name and player['Team'] == team:
                        player_scored_enough = player['Points'] > points_threshold
                        if team_won and player_scored_enough:
                            return "p2"  # Resolve to "Yes"
            return "p1"  # Resolve to "No" if conditions not met
    return "p1"  # Resolve to "No" if no relevant game found

# Main execution function
if __name__ == "__main__":
    # Extract required info directly from the question
    game_date = "2025-05-26"
    team_name = "Oklahoma City Thunder"
    player_name = "Shai Gilgeous-Alexander"
    points_needed = 32.5

    # Get the recommendation based on the game and player performance
    recommendation = check_game_and_performance(game_date, team_name, player_name, points_needed)
    print(f"recommendation: {recommendation}")