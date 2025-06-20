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
            print("Proxy failed, trying primary endpoint.")
            return make_request(endpoint, path, use_proxy=False)
        else:
            raise ConnectionError(f"Failed to retrieve data from {url}: {e}")

# Function to check player's score
def check_player_score(game_date, player_name):
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PRIMARY_ENDPOINT, f"/scores/json/GamesByDate/{formatted_date}")

    # Find the game involving the Indiana Pacers and Oklahoma City Thunder
    for game in games_today:
        if "Indiana Pacers" in game['HomeTeam'] or "Indiana Pacers" in game['AwayTeam']:
            if "Oklahoma City Thunder" in game['HomeTeam'] or "Oklahoma City Thunder" in game['AwayTeam']:
                # Get the player stats for the found game
                game_id = game['GameID']
                player_stats = make_request(PRIMARY_ENDPOINT, f"/stats/json/PlayerGameStatsByGame/{game_id}")
                for stat in player_stats:
                    if stat['Name'] == player_name:
                        points = stat['Points']
                        return points
    return None

# Main function to resolve the market
def resolve_market():
    game_date = "2025-06-11"
    player_name = "Tyrese Haliburton"
    points_threshold = 17.5

    try:
        points = check_player_score(game_date, player_name)
        if points is None:
            print("recommendation: p1")  # Player did not play or game not found
        elif points > points_threshold:
            print("recommendation: p2")  # Player scored more than 17.5 points
        else:
            print("recommendation: p1")  # Player scored 17.5 points or less
    except Exception as e:
        print(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown or error state

if __name__ == "__main__":
    resolve_market()