import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants
GAME_DATE = "2025-05-27"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Dallas Stars": "DAL"}
PLAYER_NAME = "Connor McDavid"

# Helper functions
def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if game['HomeTeam'] == TEAM_ABBREVIATIONS["Dallas Stars"] and game['AwayTeam'] == TEAM_ABBREVIATIONS["Edmonton Oilers"]:
                return game
    return None

def check_player_goals(game_id, player_name):
    url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByGame/{game_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == player_name and stat['Goals'] >= 1:
                return True
    return False

# Main execution
if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE)
    if game_info and game_info['Status'] == "Scheduled":
        player_scored = check_player_goals(game_info['GameID'], PLAYER_NAME)
        if player_scored:
            print("recommendation: p2")  # Yes, Connor McDavid scored 1+ goals
        else:
            print("recommendation: p1")  # No, Connor McDavid did not score
    else:
        print("recommendation: p1")  # Game not played or data unavailable