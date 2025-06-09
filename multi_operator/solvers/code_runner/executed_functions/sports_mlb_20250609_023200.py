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
        if endpoint == PROXY_ENDPOINT:
            print(f"Proxy failed, trying primary endpoint. Error: {e}")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"Failed to retrieve data from primary endpoint. Error: {e}")
            return None

# Function to check player's points in a specific game
def check_player_points(game_date, player_name):
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_path = f"/scores/json/GamesByDate/{formatted_date}"
    games_data = make_request(PROXY_ENDPOINT, games_path)

    if games_data:
        for game in games_data:
            if 'Oklahoma City Thunder' in [game['HomeTeam'], game['AwayTeam']]:
                game_id = game['GameID']
                stats_path = f"/stats/json/PlayerGameStatsByGame/{game_id}"
                stats_data = make_request(PROXY_ENDPOINT, stats_path)
                if stats_data:
                    for player_stats in stats_data:
                        if player_stats['Name'] == player_name:
                            points = player_stats['Points']
                            return points
    return None

# Main function to resolve the market
def resolve_market():
    game_date = "2025-06-08"
    player_name = "Shai Gilgeous-Alexander"
    points_needed = 33.5

    points = check_player_points(game_date, player_name)
    if points is None:
        print("recommendation: p1")  # No data or player did not play
    elif points > points_needed:
        print("recommendation: p2")  # Player scored more than 33.5 points
    else:
        print("recommendation: p1")  # Player scored less or equal to 33.5 points

if __name__ == "__main__":
    resolve_market()