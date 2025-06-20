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
        print(f"Error: {e}")
        return None

# Function to check player's score
def check_player_score(game_date, player_name):
    # Format date for API endpoint
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    path = f"/scores/json/PlayerGameStatsByDate/{formatted_date}"

    # Try proxy endpoint first
    data = make_request(PROXY_ENDPOINT, path)
    if data is None:
        # Fallback to primary endpoint if proxy fails
        data = make_request(PRIMARY_ENDPOINT, path)
        if data is None:
            return "p3"  # Unknown outcome if both requests fail

    # Search for player and check score
    for player_stats in data:
        if player_stats["Name"] == player_name:
            points = player_stats.get("Points", 0)
            return "p2" if points > 16.5 else "p1"

    return "p1"  # Resolve to "No" if player did not play or data not found

# Main function to run the check
def main():
    game_date = "2025-06-16"
    player_name = "Tyrese Haliburton"
    recommendation = check_player_score(game_date, player_name)
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()