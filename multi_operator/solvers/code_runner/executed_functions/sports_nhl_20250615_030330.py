import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
GAME_DATE = "2025-06-14"
PLAYER_NAME = "Evan Bouchard"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}
RESOLUTION_MAP = {"No": "p1", "Yes": "p2", "50-50": "p3"}

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        return None

# Function to find the game and check if the player scored
def check_player_score(game_date, player_name, team_abbreviations):
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{formatted_date}"
    
    # Try proxy first
    games = make_request(PROXY_ENDPOINT, HEADERS)
    if not games:
        # Fallback to primary endpoint
        games = make_request(url, HEADERS)
    
    if games:
        for game in games:
            if game['Status'] == "Final" and {game['HomeTeam'], game['AwayTeam']} == set(team_abbreviations.values()):
                game_id = game['GameID']
                player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
                player_stats = make_request(player_stats_url, HEADERS)
                if player_stats:
                    for stat in player_stats:
                        if stat['Name'] == player_name and stat['Goals'] > 0.5:
                            return "Yes"
                return "No"
    return "50-50"

# Main execution
if __name__ == "__main__":
    result = check_player_score(GAME_DATE, PLAYER_NAME, TEAM_ABBREVIATIONS)
    recommendation = RESOLUTION_MAP[result]
    print(f"recommendation: {recommendation}")