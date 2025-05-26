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

# Function to check player's points in a specific game
def check_player_points(game_date, player_name):
    # Format date for API endpoint
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_path = f"/scores/json/GamesByDate/{formatted_date}"
    
    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, games_path)
    if games is None:
        games = make_request(PRIMARY_ENDPOINT, games_path)
    
    if games:
        for game in games:
            if "Oklahoma City Thunder" in [game["HomeTeam"], game["AwayTeam"]]:
                game_id = game["GameID"]
                stats_path = f"/stats/json/PlayerGameStatsByGame/{game_id}"
                
                # Try proxy endpoint first
                player_stats = make_request(PROXY_ENDPOINT, stats_path)
                if player_stats is None:
                    player_stats = make_request(PRIMARY_ENDPOINT, stats_path)
                
                if player_stats:
                    for stat in player_stats:
                        if stat["Name"] == player_name:
                            points = stat["Points"]
                            return points
    return None

# Main function to resolve the market
def resolve_market():
    game_date = "2025-05-22"
    player_name = "Shai Gilgeous-Alexander"
    points_needed = 30.5
    
    points = check_player_points(game_date, player_name)
    if points is None:
        print("recommendation: p1")  # No data available, resolve as "No"
    elif points > points_needed:
        print("recommendation: p2")  # Yes, player scored more than 30.5 points
    else:
        print("recommendation: p1")  # No, player did not score more than 30.5 points

if __name__ == "__main__":
    resolve_market()