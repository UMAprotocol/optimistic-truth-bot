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
GAME_DATE = "2025-05-31"
TEAM_NAME = "New York Knicks"
PLAYER_NAME = "Jalen Brunson"
GAME_ID = "548482"

# URL configurations
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Function to make API requests
def make_request(url, headers, proxy=False):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if proxy:
            print(f"Error with primary endpoint, trying proxy. Error: {e}")
            proxy_url = url.replace(PRIMARY_ENDPOINT, PROXY_ENDPOINT)
            return make_request(proxy_url, headers)
        else:
            print(f"Failed to retrieve data from proxy. Error: {e}")
            return None

# Function to check game outcome and player performance
def check_game_and_performance():
    # Construct URL for game data
    game_url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}"
    game_data = make_request(game_url, HEADERS, proxy=True)
    
    if game_data:
        for game in game_data:
            if game['GameID'] == GAME_ID:
                if game['Status'] != "Final":
                    return "p1"  # Game not completed or postponed
                if game['Winner'] == TEAM_NAME:
                    # Check player performance
                    player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{GAME_ID}"
                    player_stats = make_request(player_stats_url, HEADERS, proxy=True)
                    
                    if player_stats:
                        for player in player_stats:
                            if player['Name'] == PLAYER_NAME:
                                points = player.get('Points', 0)
                                if points > 31.5:
                                    return "p2"  # Knicks win and Brunson scores 32+ points
                                else:
                                    return "p1"  # Knicks win but Brunson scores <= 31.5 points
                return "p1"  # Knicks did not win
    return "p1"  # Default to "No" if data is insufficient or game is postponed/cancelled

# Main execution
if __name__ == "__main__":
    result = check_game_and_performance()
    print(f"recommendation: {result}")