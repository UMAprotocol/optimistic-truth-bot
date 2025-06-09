import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants
GAME_DATE = "2025-06-05"
TEAMS = ("Indiana Pacers", "Oklahoma City Thunder")
PLAYER_NAME = "Tyrese Haliburton"
POINTS_THRESHOLD = 17.5

# Function to get game data
def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if game['HomeTeam'] in TEAMS and game['AwayTeam'] in TEAMS:
                return game
    return None

# Function to get player stats
def get_player_stats(game_id, player_name):
    url = f"https://api.sportsdata.io/v3/nba/stats/json/PlayerGameStatsByGame/{game_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        stats = response.json()
        for stat in stats:
            if stat['Name'] == player_name:
                return stat
    return None

# Main function to determine the outcome
def resolve_market():
    game = get_game_data(GAME_DATE)
    if not game or game['Status'] != 'Final':
        return "recommendation: p1"  # No or not final, resolve to No

    player_stats = get_player_stats(game['GameID'], PLAYER_NAME)
    if not player_stats or player_stats['Points'] <= POINTS_THRESHOLD:
        return "recommendation: p1"  # Player did not score enough points, resolve to No

    if game['Winner'] == 'Indiana Pacers':
        return "recommendation: p2"  # Pacers won and Haliburton scored enough points, resolve to Yes

    return "recommendation: p1"  # Pacers did not win, resolve to No

# Run the main function
if __name__ == "__main__":
    print(resolve_market())