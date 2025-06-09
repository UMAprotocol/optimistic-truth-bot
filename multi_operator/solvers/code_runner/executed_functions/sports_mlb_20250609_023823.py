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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

# Date and teams for the NBA Finals Game 2
GAME_DATE = "2025-06-08"
TEAM1 = "Indiana Pacers"
TEAM2 = "Oklahoma City Thunder"
PLAYER = "Tyrese Haliburton"
POINTS_THRESHOLD = 16.5

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
            if {game['HomeTeam'], game['AwayTeam']} == {TEAM1, TEAM2}:
                if game['Status'] != "Final":
                    return "p4"  # Game not completed
                # Check player performance
                player_stats_url = f"/stats/json/PlayerGameStatsByDate/{GAME_DATE}"
                player_stats_data = make_request(player_stats_url)
                if player_stats_data:
                    for stat in player_stats_data:
                        if stat['Name'] == PLAYER and stat['Team'] == TEAM1:
                            points = stat.get('Points', 0)
                            if points > POINTS_THRESHOLD and game['Winner'] == TEAM1:
                                return "p2"  # Pacers won and Haliburton scored over 16.5 points
                            break
                return "p1"  # Conditions not met
    return "p1"  # Game not found or other conditions not met

# Main execution
if __name__ == "__main__":
    result = check_game_and_player_performance()
    print(f"recommendation: {result}")