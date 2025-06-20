import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API headers
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}

# Constants for the game and player
GAME_DATE = "2025-06-17"
PLAYER_NAME = "Connor McDavid"
TEAMS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution map based on the ancillary data
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "50-50": "p3"
}

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
        return None

# Function to check if the player scored
def check_player_score(game_id, player_name):
    url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByGame/{game_id}"
    game_stats = make_request(url, HEADERS)
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
    
    # Make the API request
    games = make_request(url, HEADERS)
    if not games:
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    
    # Find the specific game
    for game in games:
        if game['HomeTeam'] in TEAMS.values() and game['AwayTeam'] in TEAMS.values():
            if game['Status'] == "Final":
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