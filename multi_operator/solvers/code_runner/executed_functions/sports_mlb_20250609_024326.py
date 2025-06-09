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
DATE = "2025-06-08"
TEAM = "Oklahoma City Thunder"
PLAYER = "Shai Gilgeous-Alexander"

# API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check game results and player performance
def check_game_and_performance():
    # Construct URL for game data
    game_date_url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{DATE}"
    games = make_request(game_date_url, HEADERS)
    if not games:
        return "p1"  # Resolve to "No" if data retrieval fails

    # Find the specific game
    for game in games:
        if TEAM in (game['HomeTeam'], game['AwayTeam']):
            if game['Status'] != "Final":
                return "p1"  # Game not completed or postponed

            # Check player performance
            player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByDate/{DATE}"
            player_stats = make_request(player_stats_url, HEADERS)
            if not player_stats:
                return "p1"  # Resolve to "No" if data retrieval fails

            # Find player stats in the game
            for stat in player_stats:
                if stat['Name'] == PLAYER and stat['Team'] == TEAM:
                    points = stat.get('Points', 0)
                    if points > 33.5 and game['Winner'] == TEAM:
                        return "p2"  # Yes, conditions met
                    break

    return "p1"  # Default to "No" if conditions are not met

# Main execution
if __name__ == "__main__":
    result = check_game_and_performance()
    print(f"recommendation: {result}")