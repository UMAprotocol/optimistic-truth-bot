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
GAME_DATE = "2025-05-31"
TEAMS = ("Indiana Pacers", "New York Knicks")
PLAYER_NAME = "Tyrese Haliburton"
POINTS_THRESHOLD = 20.5

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
            print(f"Error: {e}")
            return None

# Function to find the game and check the conditions
def check_game_and_player():
    games_url = f"/scores/json/GamesByDate/{GAME_DATE}"
    games_data = make_request(games_url)
    if games_data:
        for game in games_data:
            if {game['HomeTeam'], game['AwayTeam']} == set(TEAMS):
                if game['Status'] != "Final":
                    return "p1"  # Game not completed or postponed
                # Fetch player stats
                game_id = game['GameID']
                stats_url = f"/stats/json/PlayerGameStatsByGame/{game_id}"
                stats_data = make_request(stats_url)
                if stats_data:
                    for player_stats in stats_data:
                        if player_stats['Name'] == PLAYER_NAME:
                            points = player_stats.get('Points', 0)
                            if points > POINTS_THRESHOLD and game['Winner'] == "Indiana Pacers":
                                return "p2"  # Pacers won and Haliburton scored over 20.5 points
                            else:
                                return "p1"  # Conditions not met
    return "p1"  # Default to no if data is insufficient or conditions not met

# Main execution
if __name__ == "__main__":
    result = check_game_and_player()
    print(f"recommendation: {result}")