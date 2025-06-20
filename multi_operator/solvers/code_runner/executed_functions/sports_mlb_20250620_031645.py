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
def make_request(endpoint, path, use_proxy=False):
    url = f"{PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print(f"Proxy failed, trying primary endpoint: {e}")
            return make_request(endpoint, path, use_proxy=False)
        else:
            print(f"Request failed: {e}")
            return None

# Function to check player's score
def check_player_score(game_date, player_name):
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_path = f"/scores/json/GamesByDate/{formatted_date}"
    games_data = make_request(PRIMARY_ENDPOINT, games_path, use_proxy=True)

    if games_data:
        for game in games_data:
            if game['Status'] == 'Final':
                game_id = game['GameID']
                stats_path = f"/stats/json/PlayerGameStatsByGame/{game_id}"
                stats_data = make_request(PRIMARY_ENDPOINT, stats_path, use_proxy=True)
                if stats_data:
                    for stat in stats_data:
                        if stat['Name'] == player_name:
                            points = stat['Points']
                            return points
    return None

# Main function to resolve the market
def resolve_market():
    game_date = "2025-06-19"
    player_name = "Shai Gilgeous-Alexander"
    points_needed = 34.5

    player_points = check_player_score(game_date, player_name)
    if player_points is None:
        print("recommendation: p1")  # No data or game not found, resolve to "No"
    elif player_points > points_needed:
        print("recommendation: p2")  # Player scored more than 34.5 points, resolve to "Yes"
    else:
        print("recommendation: p1")  # Player did not score more than 34.5 points, resolve to "No"

if __name__ == "__main__":
    resolve_market()