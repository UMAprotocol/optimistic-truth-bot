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
def make_api_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_api_request(url, use_proxy=False)
        else:
            print(f"API request failed: {e}")
            return None

# Function to find player stats in a specific game
def get_player_game_stats(player_id, game_id):
    stats = make_api_request(f"/scores/json/PlayerGameStatsByPlayer/{game_id}/{player_id}")
    if stats:
        return stats.get('Points')
    return None

# Function to find game ID and player ID
def find_game_and_player(date, team, player_name):
    games = make_api_request(f"/scores/json/GamesByDate/{date}")
    player_info = make_api_request(f"/scores/json/Players/{team}")
    
    game_id = None
    player_id = None
    
    if games:
        for game in games:
            if game['HomeTeam'] == team or game['AwayTeam'] == team:
                game_id = game['GameID']
                break
    
    if player_info:
        for player in player_info:
            if player['Name'] == player_name:
                player_id = player['PlayerID']
                break
    
    return game_id, player_id

# Main function to resolve the market
def resolve_market():
    game_date = "2025-06-16"
    team = "IND"  # Indiana Pacers
    player_name = "Tyrese Haliburton"
    
    game_id, player_id = find_game_and_player(game_date, team, player_name)
    
    if not game_id or not player_id:
        print("Game or player not found.")
        return "recommendation: p1"  # Resolve to "No" if game or player not found
    
    points = get_player_game_stats(player_id, game_id)
    
    if points is None:
        print("Player stats not available.")
        return "recommendation: p1"  # Resolve to "No" if stats not available
    
    if points >= 17:
        return "recommendation: p2"  # Yes, scored 17 or more points
    else:
        return "recommendation: p1"  # No, scored less than 17 points

# Run the resolver function
if __name__ == "__main__":
    result = resolve_market()
    print(result)