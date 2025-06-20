import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}

# Constants
GAME_DATE = "2025-06-12"
PLAYER_NAME = "Carter Verhaeghe"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution map based on the outcome
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "50-50": "p3"
}

# Function to make a GET request to the API
def get_api_data(url, proxy_url=None):
    try:
        response = requests.get(proxy_url if proxy_url else url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if proxy_url:
            # Try primary endpoint if proxy fails
            return get_api_data(url)
        print(f"API request failed: {e}")
        return None

# Function to check if the player scored in the game
def check_player_score(game_id, player_name):
    url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByGame/{game_id}"
    game_stats = get_api_data(url)
    if game_stats:
        for stat in game_stats:
            if stat['Name'] == player_name and stat['Goals'] > 0:
                return True
    return False

# Main function to resolve the market
def resolve_market():
    # Construct the URL for the game data
    game_date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date_formatted}"
    
    # Get the game data
    games = get_api_data(url)
    if not games:
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    
    # Find the specific game
    for game in games:
        if {game['HomeTeam'], game['AwayTeam']} == set(TEAM_ABBREVIATIONS.values()):
            if game['Status'] == "Final":
                # Check if the player scored
                if check_player_score(game['GameID'], PLAYER_NAME):
                    return "recommendation: " + RESOLUTION_MAP["Yes"]
                else:
                    return "recommendation: " + RESOLUTION_MAP["No"]
            else:
                return "recommendation: " + RESOLUTION_MAP["50-50"]
    
    # If no game is found or not completed
    return "recommendation: " + RESOLUTION_MAP["50-50"]

# Run the main function
if __name__ == "__main__":
    result = resolve_market()
    print(result)