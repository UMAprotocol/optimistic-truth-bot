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
MIN_POINTS = 27.5

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
        print("Failed to retrieve games data.")
        return "recommendation: p1"  # Resolve to "No" if data fetch fails

    # Find the specific game
    game = next((g for g in games_data if g['HomeTeam'] == TEAM or g['AwayTeam'] == TEAM), None)
    if not game:
        print("Game not found.")
        return "recommendation: p1"  # Resolve to "No" if game is not found

    # Check if game was postponed or cancelled
    if game['Status'] != 'Final':
        print("Game was not completed.")
        return "recommendation: p1"  # Resolve to "No" if game is not completed

    # Check player performance
    player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByDate/{DATE}"
    player_stats_data = get_data(player_stats_url)
    
    if not player_stats_data:
        print("Failed to retrieve player stats data.")
        return "recommendation: p1"  # Resolve to "No" if data fetch fails

    # Find the player's performance in the game
    player_performance = next((p for p in player_stats_data if p['Name'] == PLAYER and p['Team'] == TEAM), None)
    if not player_performance:
        print("Player did not play in the game.")
        return "recommendation: p1"  # Resolve to "No" if player did not play

    # Check if player scored more than the minimum points
    if player_performance['Points'] > MIN_POINTS:
        print("Player scored more than 27.5 points.")
        if game['WinningTeam'] == TEAM:
            print("Team won the game.")
            return "recommendation: p2"  # Resolve to "Yes" if both conditions are met
    return "recommendation: p1"  # Resolve to "No" if any condition is not met

if __name__ == "__main__":
    result = check_game_and_performance()
    print(result)