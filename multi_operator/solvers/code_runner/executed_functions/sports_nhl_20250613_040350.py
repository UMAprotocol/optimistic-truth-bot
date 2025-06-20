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
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}
PLAYER_NAME = "Corey Perry"

# Resolution map based on the ancillary data
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "50-50": "p3"
}

# Function to fetch game data
def fetch_game_data(date):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} {response.reason}")

# Function to check if Corey Perry scored
def check_player_score(games):
    for game in games:
        if game['HomeTeam'] == TEAM_ABBREVIATIONS["Edmonton Oilers"] and game['AwayTeam'] == TEAM_ABBREVIATIONS["Florida Panthers"]:
            if 'PlayerGames' in game:
                for player in game['PlayerGames']:
                    if player['Name'] == PLAYER_NAME and player['Goals'] > 0:
                        return True
    return False

# Main function to resolve the market
def resolve_market():
    try:
        games = fetch_game_data(GAME_DATE)
        if not games:
            return "recommendation: " + RESOLUTION_MAP["50-50"]
        if check_player_score(games):
            return "recommendation: " + RESOLUTION_MAP["Yes"]
        else:
            return "recommendation: " + RESOLUTION_MAP["No"]
    except Exception as e:
        print(f"Error: {str(e)}")
        return "recommendation: " + RESOLUTION_MAP["50-50"]

# Run the main function
if __name__ == "__main__":
    result = resolve_market()
    print(result)