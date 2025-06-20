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
PLAYER_NAME = "Aleksander Barkov"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}
RESOLUTION_MAP = {"No": "p1", "Yes": "p2", "50-50": "p3"}

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"

# Function to make API requests
def make_api_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return None

# Function to find and analyze the game
def analyze_game():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/PlayerGameStatsByDate/{date_formatted}"
    
    # Try proxy endpoint first
    game_data = make_api_request(PROXY_ENDPOINT + url, HEADERS)
    if not game_data:
        # Fallback to primary endpoint if proxy fails
        game_data = make_api_request(url, HEADERS)
    
    if not game_data:
        return "p4"  # Unable to fetch data

    # Check for player's performance in the game
    for game in game_data:
        if game['Name'] == PLAYER_NAME and game['Team'] in TEAM_ABBREVIATIONS.values():
            goals = game.get('Goals', 0)
            if goals > 0.5:
                return RESOLUTION_MAP["Yes"]
            else:
                return RESOLUTION_MAP["No"]

    # If no data found for player, assume game not completed
    return RESOLUTION_MAP["50-50"]

# Main execution
if __name__ == "__main__":
    result = analyze_game()
    print(f"recommendation: {result}")