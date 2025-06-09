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

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check player's points in a specific game
def check_player_points(game_date, player_name, points_threshold):
    # Format the date for the API endpoint
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    path = f"/scores/json/PlayerGameStatsByDate/{formatted_date}"

    # Try proxy endpoint first
    data = make_request(PROXY_ENDPOINT, path)
    if data is None:
        # Fallback to primary endpoint if proxy fails
        data = make_request(PRIMARY_ENDPOINT, path)
        if data is None:
            return "p4"  # Unable to resolve due to API failure

    # Search for the player and check points
    for game_stats in data:
        if game_stats["Name"] == player_name:
            points_scored = game_stats["Points"]
            if points_scored is not None:
                return "p2" if points_scored > points_threshold else "p1"
            else:
                return "p4"  # Player stats not available

    return "p1"  # Player did not play or game data not found

# Main function to resolve the market
def resolve_market():
    game_date = "2025-06-08"
    player_name = "Shai Gilgeous-Alexander"
    points_threshold = 33.5

    recommendation = check_player_points(game_date, player_name, points_threshold)
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    resolve_market()