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

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}/{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check the player's performance in a specific game
def check_player_performance(game_date, player_name):
    # Format the date for the API endpoint
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_on_date = make_request(PROXY_ENDPOINT, f"GamesByDate/{formatted_date}")
    if not games_on_date:
        games_on_date = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{formatted_date}")
    
    if games_on_date:
        for game in games_on_date:
            if game['Status'] == 'Final':
                player_stats = make_request(PROXY_ENDPOINT, f"PlayerGameStatsByDate/{formatted_date}/{player_name}")
                if not player_stats:
                    player_stats = make_request(PRIMARY_ENDPOINT, f"PlayerGameStatsByDate/{formatted_date}/{player_name}")
                
                if player_stats and player_stats['Scoring']['Goals'] > 0.5:
                    return "p2"  # Player scored more than 0.5 goals
        return "p1"  # No goals or game not final
    return "p4"  # No data available or game not found

# Main function to resolve the market
def resolve_market():
    game_date = "2025-05-31"
    player_name = "Calhanoglu Hakan"
    result = check_player_performance(game_date, player_name)
    print(f"recommendation: {result}")

# Run the resolver
if __name__ == "__main__":
    resolve_market()