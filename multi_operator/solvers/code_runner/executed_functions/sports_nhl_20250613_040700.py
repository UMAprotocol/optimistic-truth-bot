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

# Constants
GAME_DATE = "2025-06-12"
PLAYER_NAME = "Carter Verhaeghe"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution map based on the ancillary data
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scores more than 0.5 goals
    "No": "p1",   # Player does not score more than 0.5 goals
    "50-50": "p3" # Game not completed by the specified date
}

# Function to check if the player scored in the game
def check_player_score(game_id, player_name):
    url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByGame/{game_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        stats = response.json()
        for stat in stats:
            if stat['Name'] == player_name and stat['Goals'] > 0.5:
                return "Yes"
        return "No"
    return "50-50"

# Function to find the game ID
def find_game_id(date, team1, team2):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if game['HomeTeam'] == team1 and game['AwayTeam'] == team2:
                return game['GameID']
            if game['HomeTeam'] == team2 and game['AwayTeam'] == team1:
                return game['GameID']
    return None

# Main function to resolve the market
def resolve_market():
    current_date = datetime.now()
    deadline_date = datetime.strptime("2025-12-31 23:59", "%Y-%m-%d %H:%M")
    if current_date > deadline_date:
        return "recommendation: " + RESOLUTION_MAP["50-50"]

    team1 = TEAM_ABBREVIATIONS["Edmonton Oilers"]
    team2 = TEAM_ABBREVIATIONS["Florida Panthers"]
    game_id = find_game_id(GAME_DATE, team1, team2)
    if game_id:
        result = check_player_score(game_id, PLAYER_NAME)
        return "recommendation: " + RESOLUTION_MAP[result]
    return "recommendation: " + RESOLUTION_MAP["50-50"]

# Execute the function and print the result
if __name__ == "__main__":
    print(resolve_market())