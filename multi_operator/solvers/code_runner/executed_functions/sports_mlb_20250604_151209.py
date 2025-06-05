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

# Game and player details
GAME_DATE = "2025-05-31"
TEAM_NAME = "New York Knicks"
PLAYER_NAME = "Jalen Brunson"

# Resolution map
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1"
}

def get_game_data():
    # Format the date for the API endpoint
    formatted_date = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%b-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{formatted_date}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        
        # Find the game involving the specified team
        for game in games:
            if TEAM_NAME in (game['HomeTeam'], game['AwayTeam']):
                return game
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return None

def get_player_stats(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        player_stats = response.json()
        
        # Find the stats for the specified player
        for stat in player_stats:
            if stat['Name'] == player_name:
                return stat
    except requests.RequestException as e:
        print(f"Error fetching player stats: {e}")
        return None

def resolve_market():
    game = get_game_data()
    if not game:
        return "recommendation: " + RESOLUTION_MAP["No"]
    
    if game['Status'] != "Final":
        return "recommendation: " + RESOLUTION_MAP["No"]
    
    player_stats = get_player_stats(game['GameID'], PLAYER_NAME)
    if not player_stats:
        return "recommendation: " + RESOLUTION_MAP["No"]
    
    knicks_win = (game['HomeTeam'] == TEAM_NAME and game['HomeTeamScore'] > game['AwayTeamScore']) or \
                 (game['AwayTeam'] == TEAM_NAME and game['AwayTeamScore'] > game['HomeTeamScore'])
    brunson_scores_32_plus = player_stats['Points'] > 31.5
    
    if knicks_win and brunson_scores_32_plus:
        return "recommendation: " + RESOLUTION_MAP["Yes"]
    else:
        return "recommendation: " + RESOLUTION_MAP["No"]

if __name__ == "__main__":
    result = resolve_market()
    print(result)