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
GAME_DATE = "2025-06-12"
PLAYER_NAME = "Matthew Tkachuk"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}
RESOLUTION_MAP = {"No": "p1", "Yes": "p2", "50-50": "p3"}

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

# Function to check if Matthew Tkachuk scored in the game
def check_player_score(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    game_stats = make_request(url, HEADERS)
    if game_stats:
        for stat in game_stats:
            if stat["Name"] == player_name and stat["Goals"] > 0:
                return True
    return False

# Main function to resolve the market
def resolve_market():
    # Construct the URL to find the game
    game_date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date_formatted}"
    
    # Make the request
    games = make_request(url, HEADERS)
    if games:
        for game in games:
            if game["HomeTeam"] in TEAM_ABBREVIATIONS.values() and game["AwayTeam"] in TEAM_ABBREVIATIONS.values():
                if check_player_score(game["GameID"], PLAYER_NAME):
                    return "recommendation: " + RESOLUTION_MAP["Yes"]
                else:
                    return "recommendation: " + RESOLUTION_MAP["No"]
    
    # If the game has not been completed by the end of 2025
    current_date = datetime.now()
    if current_date > datetime.strptime("2025-12-31 23:59", "%Y-%m-%d %H:%M"):
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    
    return "recommendation: " + RESOLUTION_MAP["No"]

# Run the main function
if __name__ == "__main__":
    result = resolve_market()
    print(result)