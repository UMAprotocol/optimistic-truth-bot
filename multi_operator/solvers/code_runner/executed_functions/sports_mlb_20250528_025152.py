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
            print("Proxy failed, trying primary endpoint")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"Error: {e}")
            return None

# Function to check Jalen Brunson's points
def check_jalen_brunson_points(game_date):
    path = f"/scores/json/GamesByDate/{game_date}"
    games = make_request(PROXY_ENDPOINT, path)
    if games:
        for game in games:
            if game['Status'] == 'Final' and ('New York' in game['HomeTeam'] or 'New York' in game['AwayTeam']):
                game_id = game['GameID']
                player_stats_path = f"/stats/json/PlayerGameStatsByGame/{game_id}"
                player_stats = make_request(PROXY_ENDPOINT, player_stats_path)
                if player_stats:
                    for stat in player_stats:
                        if stat['Name'] == 'Jalen Brunson':
                            points = stat['Points']
                            return points >= 30
    return False

# Main function to resolve the market
def resolve_market():
    game_date = "2025-05-27"
    if check_jalen_brunson_points(game_date):
        return "recommendation: p2"  # Yes, scored 30+ points
    else:
        return "recommendation: p1"  # No, did not score 30+ points

# Run the resolution function and print the result
if __name__ == "__main__":
    result = resolve_market()
    print(result)