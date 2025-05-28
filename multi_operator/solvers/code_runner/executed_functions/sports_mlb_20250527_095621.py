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
def make_request(endpoint, path, params=None, use_proxy=False):
    url = f"{PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT}{path}"
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint")
            return make_request(endpoint, path, params, use_proxy=False)
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
    game_info = next((game for game in games_today if team in [game['HomeTeam'], game['AwayTeam']]), None)
    if not game_info:
        return "p1"  # Game not found, resolve as "No"

    # Check if the game was postponed or cancelled
    if game_info['Status'] != 'Final':
        return "p1"  # Game not completed on the specified date, resolve as "No"

    # Check game outcome
    thunder_won = (game_info['Winner'] == team)

    # Get player stats
    game_id = game_info['GameID']
    player_stats = make_request(PRIMARY_ENDPOINT, f"/stats/json/PlayerGameStatsByGame/{game_id}", use_proxy=True)
    player_performance = next((stat for stat in player_stats if stat['Name'] == player_name), None)

    if not player_performance:
        return "p1"  # Player did not play or data missing, resolve as "No"

    # Check if player scored more than the threshold
    player_scored_enough = (player_performance['Points'] > points_threshold)

    # Final resolution based on both conditions
    if thunder_won and player_scored_enough:
        return "p2"  # Yes
    else:
        return "p1"  # No

# Main execution function
def main():
    # Specific details from the question
    game_date = "2025-05-26"
    team = "Oklahoma City Thunder"
    player_name = "Shai Gilgeous-Alexander"
    points_threshold = 32.5

    # Get the recommendation based on the game and player performance
    recommendation = check_game_and_performance(game_date, team, player_name, points_threshold)
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()