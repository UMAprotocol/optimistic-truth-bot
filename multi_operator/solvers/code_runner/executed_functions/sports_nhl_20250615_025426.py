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

# Constants for the game and player
GAME_DATE = "2025-06-14"
PLAYER_NAME = "Aleksander Barkov"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution map based on the ancillary data
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scores more than 0.5 goals
    "No": "p1",   # Player scores 0.5 goals or less
    "50-50": "p3" # Game not completed by the specified date
}

# Function to get game data
def get_game_data():
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{GAME_DATE}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if game['HomeTeam'] in TEAM_ABBREVIATIONS.values() and game['AwayTeam'] in TEAM_ABBREVIATIONS.values():
                return game
    return None

# Function to check player's performance
def check_player_performance(game_id):
    url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByGame/{game_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == PLAYER_NAME:
                goals = stat['Goals']
                return "Yes" if goals > 0.5 else "No"
    return "No"

# Main function to determine the outcome
def determine_outcome():
    current_date = datetime.now()
    deadline_date = datetime.strptime("2025-12-31 23:59", "%Y-%m-%d %H:%M")
    
    if current_date > deadline_date:
        return RESOLUTION_MAP["50-50"]
    
    game = get_game_data()
    if game:
        game_id = game['GameID']
        result = check_player_performance(game_id)
        return RESOLUTION_MAP[result]
    else:
        return RESOLUTION_MAP["50-50"]

# Run the main function and print the recommendation
if __name__ == "__main__":
    recommendation = determine_outcome()
    print("recommendation:", recommendation)