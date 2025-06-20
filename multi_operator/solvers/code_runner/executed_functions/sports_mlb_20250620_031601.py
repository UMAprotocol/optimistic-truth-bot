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
            print("Proxy failed, trying primary endpoint...")
            return make_request(endpoint, path, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to check player's score
def check_player_score(game_date, player_name):
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games = make_request(PRIMARY_ENDPOINT, f"/scores/json/GamesByDate/{formatted_date}")
    if games:
        for game in games:
            if game['Status'] == 'Final':
                game_id = game['GameID']
                stats = make_request(PRIMARY_ENDPOINT, f"/stats/json/PlayerGameStatsByGame/{game_id}")
                if stats:
                    for stat in stats:
                        if stat['Name'] == player_name:
                            points = stat['Points']
                            return points
    return None

# Main function to resolve the market
def resolve_market():
    game_date = "2025-06-19"
    player_name = "Shai Gilgeous-Alexander"
    points_needed = 34.5

    score = check_player_score(game_date, player_name)
    if score is None:
        print("recommendation: p1")  # No data or game not final
    elif score > points_needed:
        print("recommendation: p2")  # Player scored more than 34.5 points
    else:
        print("recommendation: p1")  # Player did not score more than 34.5 points

if __name__ == "__main__":
    resolve_market()