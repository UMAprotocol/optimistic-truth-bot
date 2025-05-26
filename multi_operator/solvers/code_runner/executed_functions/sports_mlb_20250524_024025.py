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

# Game and player details
GAME_DATE = "2025-05-23"
TEAM_NAME = "New York Knicks"
PLAYER_NAME = "Jalen Brunson"

# Function to make API requests
def make_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(url, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to find the game and check the conditions
def check_game_and_player_performance():
    games_url = f"/scores/json/GamesByDate/{GAME_DATE}"
    games_data = make_request(games_url)
    if games_data:
        for game in games_data:
            if game['Status'] == 'Final' and (game['HomeTeam'] == TEAM_NAME or game['AwayTeam'] == TEAM_NAME):
                game_id = game['GameID']
                player_stats_url = f"/stats/json/PlayerGameStatsByGame/{game_id}"
                player_stats_data = make_request(player_stats_url)
                if player_stats_data:
                    for player_stats in player_stats_data:
                        if player_stats['Name'] == PLAYER_NAME and player_stats['Points'] > 29.5:
                            if (game['HomeTeam'] == TEAM_NAME and game['HomeTeamScore'] > game['AwayTeamScore']) or \
                               (game['AwayTeam'] == TEAM_NAME and game['AwayTeamScore'] > game['HomeTeamScore']):
                                return "p2"  # Knicks win and Brunson scores 30+ points
    return "p1"  # Conditions not met

# Main execution
if __name__ == "__main__":
    result = check_game_and_player_performance()
    print(f"recommendation: {result}")