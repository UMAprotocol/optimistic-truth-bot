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
DATE = "2025-05-26"
TEAM = "Oklahoma City Thunder"
PLAYER = "Shai Gilgeous-Alexander"
POINTS_THRESHOLD = 32.5

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error during API request: {e}")
        return None

# Function to check game result and player performance
def check_game_and_performance():
    # Construct URL for game data
    game_date_url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{DATE}"
    games_data = make_request(game_date_url, HEADERS)
    
    if not games_data:
        print("Failed to retrieve game data.")
        return "recommendation: p1"  # Default to "No" if data retrieval fails

    # Find the specific game
    for game in games_data:
        if TEAM in (game['HomeTeam'], game['AwayTeam']):
            if game['Status'] != "Final":
                return "recommendation: p1"  # Game not completed or postponed

            # Check player performance
            player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByDate/{DATE}"
            player_stats = make_request(player_stats_url, HEADERS)
            
            if not player_stats:
                print("Failed to retrieve player stats.")
                return "recommendation: p1"  # Default to "No" if data retrieval fails

            # Find the player and check points
            for player in player_stats:
                if player['Name'] == PLAYER and player['Team'] == TEAM:
                    points = player.get('Points', 0)
                    if points > POINTS_THRESHOLD and game['Winner'] == TEAM:
                        return "recommendation: p2"  # Yes, conditions met
                    break

    return "recommendation: p1"  # Default to "No" if conditions not met

# Main execution
if __name__ == "__main__":
    result = check_game_and_performance()
    print(result)