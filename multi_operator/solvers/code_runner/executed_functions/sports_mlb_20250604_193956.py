import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map for outcomes
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "50-50": "p3"
}

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check player's goal in a specific game
def check_player_goal(player_name, game_date):
    # Format date for API request
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games = make_request(PROXY_ENDPOINT, f"GamesByDate/{formatted_date}")
    if not games:
        games = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{formatted_date}")
    if games:
        for game in games:
            if game['Status'] == 'Final':
                for player in game['PlayerStats']:
                    if player['Name'] == player_name and player['Goals'] > 0.5:
                        return "Yes"
    return "No"

# Main function to resolve the market
def resolve_market():
    player_name = "Hakimi Achraf"
    game_date = "2025-05-31"
    result = check_player_goal(player_name, game_date)
    return f"recommendation: {RESOLUTION_MAP[result]}"

# Execute the function and print the result
if __name__ == "__main__":
    print(resolve_market())