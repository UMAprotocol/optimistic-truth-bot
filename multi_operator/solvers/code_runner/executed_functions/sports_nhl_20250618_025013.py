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
GAME_DATE = "2025-06-17"
PLAYER_NAME = "Connor McDavid"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}
RESOLUTION_MAP = {"No": "p1", "Yes": "p2", "50-50": "p3"}

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"

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
    current_date = datetime.now().strftime("%Y-%m-%d")
    if game_date > current_date:
        return "Too early to resolve"
    elif game_date < current_date:
        return "Completed"
    else:
        return "In progress"

# Function to find the game and check if the player scored
def check_player_goal(game_date, player_name):
    game_status = check_game_completion(game_date)
    if game_status == "Too early to resolve":
        return RESOLUTION_MAP["50-50"]
    elif game_status == "In progress":
        return RESOLUTION_MAP["50-50"]

    # Construct the URL for the game day
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date}"
    games = make_request(url, HEADERS)
    if not games:
        return RESOLUTION_MAP["50-50"]

    # Find the specific game
    for game in games:
        if game['HomeTeam'] in TEAM_ABBREVIATIONS.values() and game['AwayTeam'] in TEAM_ABBREVIATIONS.values():
            # Check player stats
            game_id = game['GameID']
            player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
            player_stats = make_request(player_stats_url, HEADERS)
            if player_stats:
                for stat in player_stats:
                    if stat['Name'] == player_name and stat['Goals'] > 0.5:
                        return RESOLUTION_MAP["Yes"]
            return RESOLUTION_MAP["No"]

    return RESOLUTION_MAP["50-50"]

# Main function to run the program
if __name__ == "__main__":
    result = check_player_goal(GAME_DATE, PLAYER_NAME)
    print(f"recommendation: {result}")