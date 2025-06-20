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
PLAYER_NAME = "Evan Bouchard"
TEAMS = ["EDM", "FLA"]  # Edmonton Oilers and Florida Panthers
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "50-50": "p3"
}

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}

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
        print(f"Error: {e}")
        return None

# Function to check if the player scored
def check_player_score(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    game_stats = make_request(url, HEADERS)
    if game_stats:
        for stat in game_stats:
            if stat['Name'] == player_name and stat['Goals'] > 0:
                return True
    return False

# Function to find the game ID
def find_game_id(game_date, teams):
    date_str = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_str}"
    games = make_request(url, HEADERS)
    if games:
        for game in games:
            if game['HomeTeam'] in teams and game['AwayTeam'] in teams:
                return game['GameID']
    return None

# Main function to resolve the market
def resolve_market():
    game_id = find_game_id(GAME_DATE, TEAMS)
    if not game_id:
        print("Game not found or not yet played.")
        return "recommendation: p4"

    if check_player_score(game_id, PLAYER_NAME):
        result = "Yes"
    else:
        result = "No"

    recommendation = RESOLUTION_MAP.get(result, "p4")
    print(f"recommendation: {recommendation}")

# Run the resolution function
if __name__ == "__main__":
    resolve_market()