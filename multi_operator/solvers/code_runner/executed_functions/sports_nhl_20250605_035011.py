import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Game and player details
GAME_DATE = "2025-06-04"
TEAM_ABBR_EDMONTON = "EDM"
TEAM_ABBR_FLORIDA = "FLA"
PLAYER_NAME = "Connor McDavid"

# Resolution conditions
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "Unknown": "p3"
}

def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def check_player_goals(player_stats, player_name):
    for stat in player_stats:
        if stat['Name'] == player_name and stat['Goals'] >= 1:
            return True
    return False

def resolve_market():
    # Try proxy endpoint first
    games_url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}"
    games_data = get_data(games_url, HEADERS)
    
    # Fallback to primary endpoint if proxy fails
    if not games_data:
        games_url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}"
        games_data = get_data(games_url, HEADERS)
    
    if not games_data:
        return "recommendation: " + RESOLUTION_MAP["Unknown"]

    # Find the specific game
    for game in games_data:
        if game['HomeTeam'] == TEAM_ABBR_FLORIDA and game['AwayTeam'] == TEAM_ABBR_EDMONTON:
            if game['Status'] != "Final":
                return "recommendation: " + RESOLUTION_MAP["No"]
            
            # Fetch player stats
            game_id = game['GameID']
            player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
            player_stats = get_data(player_stats_url, HEADERS)
            
            if player_stats and check_player_goals(player_stats, PLAYER_NAME):
                return "recommendation: " + RESOLUTION_MAP["Yes"]
            else:
                return "recommendation: " + RESOLUTION_MAP["No"]
    
    return "recommendation: " + RESOLUTION_MAP["Unknown"]

if __name__ == "__main__":
    result = resolve_market()
    print(result)