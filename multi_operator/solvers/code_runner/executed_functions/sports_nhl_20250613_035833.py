import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants for the game and player in question
GAME_DATE = "2025-06-12"
PLAYER_NAME = "Aleksander Barkov"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution conditions mapped to outcomes
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
    except requests.RequestException as e:
        print(f"Error during API request: {e}")
        return None

# Function to check if the player scored in the game
def check_player_score(game_id, player_name):
    url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByGame/{game_id}"
    game_stats = make_request(url, HEADERS)
    if game_stats:
        for stat in game_stats:
            if stat["Name"] == player_name and stat["Goals"] > 0:
                return True
    return False

# Main function to resolve the market
def resolve_market():
    # Convert game date to datetime object
    game_datetime = datetime.strptime(GAME_DATE, "%Y-%m-%d")
    current_datetime = datetime.now()

    # Check if the current date is past the game date
    if current_datetime > game_datetime:
        # Find the game ID
        url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{GAME_DATE}"
        games = make_request(url, HEADERS)
        if games:
            for game in games:
                if game["HomeTeam"] in TEAM_ABBREVIATIONS.values() and game["AwayTeam"] in TEAM_ABBREVIATIONS.values():
                    game_id = game["GameID"]
                    if check_player_score(game_id, PLAYER_NAME):
                        return "recommendation: " + RESOLUTION_MAP["Yes"]
                    else:
                        return "recommendation: " + RESOLUTION_MAP["No"]
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    else:
        return "recommendation: " + RESOLUTION_MAP["50-50"]

# Run the main function
if __name__ == "__main__":
    result = resolve_market()
    print(result)