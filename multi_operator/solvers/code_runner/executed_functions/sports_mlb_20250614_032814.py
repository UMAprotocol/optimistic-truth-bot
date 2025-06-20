import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers and API endpoints
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
            print("Proxy failed, trying primary endpoint")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"Error: {e}")
            return None

# Function to check player's points in a specific game
def check_player_points(game_date, player_name):
    formatted_date = game_date.strftime("%Y-%m-%d")
    games = make_request(PROXY_ENDPOINT, f"/scores/json/GamesByDate/{formatted_date}")
    if games:
        for game in games:
            if game['Status'] == 'Final':
                player_stats = make_request(PROXY_ENDPOINT, f"/stats/json/PlayerGameStatsByDate/{formatted_date}")
                if player_stats:
                    for stat in player_stats:
                        if stat['Name'] == player_name and stat['Points'] >= 34:
                            return "p2"  # Yes, player scored 34+ points
    return "p1"  # No, player did not score 34+ points or game data not available

# Main function to resolve the market
def resolve_market():
    game_date = datetime(2025, 6, 13, 20, 30)  # NBA Finals Game 4 date and time
    player_name = "Shai Gilgeous-Alexander"
    current_time = datetime.now()

    if current_time < game_date:
        return "p4"  # Too early to resolve
    else:
        result = check_player_points(game_date, player_name)
        return f"recommendation: {result}"

# Run the resolver function
if __name__ == "__main__":
    print(resolve_market())