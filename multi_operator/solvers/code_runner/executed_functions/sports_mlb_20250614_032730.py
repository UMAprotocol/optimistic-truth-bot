import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
DATE = "2025-06-13"
PLAYER_NAME = "Shai Gilgeous-Alexander"
TEAM = "Oklahoma City Thunder"
OPPONENT_TEAM = "Indiana Pacers"
GAME_DATE = datetime.strptime(DATE, "%Y-%m-%d")

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Function to make API requests
def make_request(url, headers, tag="API Request"):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"{tag} failed: {e}")
        return None

# Function to find the game and check player's points
def check_player_points():
    # Construct URL for games on the specific date
    games_url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{DATE}"
    games_data = make_request(games_url, HEADERS, "Games By Date")

    if not games_data:
        return "p4"  # Unable to retrieve data

    # Find the specific game
    game_id = None
    for game in games_data:
        if (game['HomeTeam'] == TEAM or game['AwayTeam'] == TEAM) and \
           (game['HomeTeam'] == OPPONENT_TEAM or game['AwayTeam'] == OPPONENT_TEAM):
            game_id = game['GameID']
            break

    if not game_id:
        return "p1"  # Game not found or not scheduled correctly

    # Get player stats for the game
    player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByDate/{DATE}"
    player_stats_data = make_request(player_stats_url, HEADERS, "Player Stats By Date")

    if not player_stats_data:
        return "p4"  # Unable to retrieve player stats

    # Check points scored by Shai Gilgeous-Alexander
    for stat in player_stats_data:
        if stat['Name'] == PLAYER_NAME and stat['Team'] == TEAM:
            points_scored = stat['Points']
            return "p2" if points_scored > 33.5 else "p1"

    return "p1"  # Player did not play or did not score enough points

# Main execution
if __name__ == "__main__":
    result = check_player_points()
    print(f"recommendation: {result}")