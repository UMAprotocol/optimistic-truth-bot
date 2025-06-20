import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
GAME_DATE = "2025-06-17"
PLAYER_NAME = "Leon Draisaitl"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}

# API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check if the game has occurred and if the player scored
def check_player_score(game_date, player_name):
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{formatted_date}"
    
    # Try proxy first
    games = make_request(PROXY_ENDPOINT + url, HEADERS)
    if games is None:
        # Fallback to primary endpoint
        games = make_request(url, HEADERS)
    
    if games:
        for game in games:
            if game['Status'] == 'Final' and {game['HomeTeam'], game['AwayTeam']} == set(TEAM_ABBREVIATIONS.values()):
                # Check player stats
                game_id = game['GameID']
                player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
                
                # Try proxy first
                player_stats = make_request(PROXY_ENDPOINT + player_stats_url, HEADERS)
                if player_stats is None:
                    # Fallback to primary endpoint
                    player_stats = make_request(player_stats_url, HEADERS)
                
                if player_stats:
                    for stat in player_stats:
                        if stat['Name'] == player_name and stat['Goals'] > 0.5:
                            return "p2"  # Player scored more than 0.5 goals
    return "p1"  # Player did not score more than 0.5 goals or game data not available

# Main execution
if __name__ == "__main__":
    result = check_player_score(GAME_DATE, PLAYER_NAME)
    print(f"recommendation: {result}")