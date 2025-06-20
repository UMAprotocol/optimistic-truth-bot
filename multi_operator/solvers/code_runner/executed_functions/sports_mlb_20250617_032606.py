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

# Function to check player's points in a specific game
def check_player_points(game_date, player_name):
    # Format the date for the API endpoint
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_path = f"/scores/json/GamesByDate/{formatted_date}"

    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, games_path)
    if games is None:
        # Fallback to primary endpoint
        games = make_request(PRIMARY_ENDPOINT, games_path)
        if games is None:
            return "p4"  # Unable to retrieve data

    # Find the game involving the specified teams
    for game in games:
        if game['HomeTeam'] == 'OKC' and game['AwayTeam'] == 'IND':
            game_id = game['GameID']
            break
    else:
        return "p4"  # Game not found

    # Get player stats for the game
    player_stats_path = f"/stats/json/PlayerGameStatsByGame/{game_id}"
    player_stats = make_request(PROXY_ENDPOINT, player_stats_path)
    if player_stats is None:
        player_stats = make_request(PRIMARY_ENDPOINT, player_stats_path)
        if player_stats is None:
            return "p4"  # Unable to retrieve data

    # Check if the player played and scored more than 34.5 points
    for stat in player_stats:
        if stat['Name'] == player_name:
            points = stat['Points']
            return "p2" if points > 34.5 else "p1"

    return "p1"  # Player did not play or did not score enough points

# Main function to run the check
if __name__ == "__main__":
    game_date = "2025-06-16"
    player_name = "Shai Gilgeous-Alexander"
    recommendation = check_player_points(game_date, player_name)
    print(f"recommendation: {recommendation}")