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
GAME_DATE = "2025-06-12"
PLAYER_NAME = "Matthew Tkachuk"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}
GAME_ID = "551594"

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
        print(f"Error during API request: {e}")
        return None

# Function to check if the game has been completed
def check_game_completion(game_date):
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date}"
    games = make_request(url, HEADERS)
    if games:
        for game in games:
            if game['GameID'] == GAME_ID and game['Status'] == 'Final':
                return True
    return False

# Function to check if player scored a goal
def check_player_goals(game_date, player_name):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByDate/{game_date}"
    player_stats = make_request(url, HEADERS)
    if player_stats:
        for stat in player_stats:
            if stat['Name'] == player_name and stat['Goals'] > 0:
                return True
    return False

# Main function to determine the market resolution
def resolve_market():
    if not check_game_completion(GAME_DATE):
        print("recommendation: p4")  # Game not completed
        return

    if check_player_goals(GAME_DATE, PLAYER_NAME):
        print("recommendation: p2")  # Player scored more than 0.5 goals
    else:
        print("recommendation: p1")  # Player did not score more than 0.5 goals

# Run the resolution function
if __name__ == "__main__":
    resolve_market()