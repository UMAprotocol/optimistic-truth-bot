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

# Function to check Jalen Brunson's points
def check_jalen_brunson_points(game_date, team_id):
    path = f"/scores/json/PlayerGameStatsByDate/{game_date}"
    data = make_request(PROXY_ENDPOINT, path) or make_request(PRIMARY_ENDPOINT, path)
    if data:
        for game in data:
            if game['TeamID'] == team_id and game['PlayerID'] == 20002571:  # Jalen Brunson's PlayerID
                points = game.get('Points', 0)
                return points
    return None

# Main function to resolve the market
def resolve_market():
    game_date = "2025-05-29"
    knicks_team_id = 24  # New York Knicks TeamID
    points = check_jalen_brunson_points(game_date, knicks_team_id)
    if points is None:
        print("recommendation: p1")  # No data available, resolve as "No"
    elif points > 30.5:
        print("recommendation: p2")  # Yes, Jalen Brunson scored more than 30.5 points
    else:
        print("recommendation: p1")  # No, Jalen Brunson did not score more than 30.5 points

# Run the main function
if __name__ == "__main__":
    resolve_market()