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
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
GAME_DATE = "2025-06-17"
PLAYER_NAME = "Evan Bouchard"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}
RESOLUTION_MAP = {"No": "p1", "Yes": "p2", "50-50": "p3"}

# Helper functions
def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    return None

def check_player_goals(game_data, player_name):
    for game in game_data:
        if game['Status'] == 'Final' and {game['HomeTeam'], game['AwayTeam']} == set(TEAM_ABBREVIATIONS.values()):
            player_stats_url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByDate/{GAME_DATE}/{game['GameID']}"
            player_stats_response = requests.get(player_stats_url, headers=HEADERS)
            if player_stats_response.status_code == 200:
                player_stats = player_stats_response.json()
                for stat in player_stats:
                    if stat['Name'] == player_name and stat['Goals'] > 0.5:
                        return True
    return False

# Main execution
def main():
    game_data = get_game_data(GAME_DATE)
    if not game_data:
        print("recommendation:", RESOLUTION_MAP["50-50"])
        return

    if check_player_goals(game_data, PLAYER_NAME):
        print("recommendation:", RESOLUTION_MAP["Yes"])
    else:
        print("recommendation:", RESOLUTION_MAP["No"])

if __name__ == "__main__":
    main()