import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Constants
DATE = "2025-05-22"
TEAM = "Oklahoma City Thunder"
PLAYER = "Shai Gilgeous-Alexander"
POINTS_THRESHOLD = 30.5
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "Unknown": "p3"
}

# API Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
NBA_SCORES_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/"
NBA_STATS_ENDPOINT = "https://api.sportsdata.io/v3/nba/stats/json/PlayerGameStatsByDate/"

# Function to get games by date
def get_games_by_date(date):
    url = f"{NBA_SCORES_ENDPOINT}{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    return None

# Function to get player stats by date
def get_player_stats_by_date(date, player_id):
    url = f"{NBA_STATS_ENDPOINT}{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        stats = response.json()
        for stat in stats:
            if stat['PlayerID'] == player_id:
                return stat
    return None

# Main function to determine the outcome
def determine_outcome():
    games = get_games_by_date(DATE)
    if not games:
        return RESOLUTION_MAP["Unknown"]

    game_info = next((game for game in games if TEAM in [game['HomeTeam'], game['AwayTeam']]), None)
    if not game_info:
        return RESOLUTION_MAP["No"]

    if game_info['Status'] != "Final":
        return RESOLUTION_MAP["No"]

    player_stats = get_player_stats_by_date(DATE, game_info['GameID'])
    if not player_stats:
        return RESOLUTION_MAP["No"]

    thunder_won = (game_info['Winner'] == TEAM)
    sga_scored_enough = (player_stats['Points'] > POINTS_THRESHOLD)

    if thunder_won and sga_scored_enough:
        return RESOLUTION_MAP["Yes"]
    else:
        return RESOLUTION_MAP["No"]

# Output the result
if __name__ == "__main__":
    result = determine_outcome()
    print(f"recommendation: {result}")