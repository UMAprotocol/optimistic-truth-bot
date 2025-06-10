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
DATE = "2025-05-31"
TEAM = "Indiana Pacers"
PLAYER = "Tyrese Haliburton"
POINTS_THRESHOLD = 20.5
GAME_ID = "548486"  # Example game ID, this would normally be dynamically determined

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Function to make API requests
def make_api_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check game outcome and player performance
def check_game_and_performance():
    # Construct URL for game details
    game_url = f"{PRIMARY_ENDPOINT}/scores/json/Game/{GAME_ID}"
    game_data = make_api_request(game_url)
    
    if not game_data:
        print("Failed to retrieve game data, trying proxy...")
        game_url = f"{PROXY_ENDPOINT}/scores/json/Game/{GAME_ID}"
        game_data = make_api_request(game_url)
        if not game_data:
            return "recommendation: p1"  # Resolve to "No" if data cannot be retrieved

    # Check if game was played and get the winning team
    if game_data['Status'] != 'Final':
        return "recommendation: p1"  # Game not completed or cancelled

    winning_team = game_data['Winner']
    if winning_team != TEAM:
        return "recommendation: p1"  # Pacers did not win

    # Check player performance
    player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{GAME_ID}"
    player_stats = make_api_request(player_stats_url)
    
    if not player_stats:
        print("Failed to retrieve player stats, trying proxy...")
        player_stats_url = f"{PROXY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{GAME_ID}"
        player_stats = make_api_request(player_stats_url)
        if not player_stats:
            return "recommendation: p1"  # Resolve to "No" if data cannot be retrieved

    # Find player and check points
    for player in player_stats:
        if player['Name'] == PLAYER and player['Points'] > POINTS_THRESHOLD:
            return "recommendation: p2"  # Both conditions met

    return "recommendation: p1"  # Player did not score enough points

# Main execution
if __name__ == "__main__":
    result = check_game_and_performance()
    print(result)