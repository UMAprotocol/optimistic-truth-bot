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

# Constants
GAME_DATE = "2025-06-14"
PLAYER_NAME = "Sam Reinhart"
TEAMS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Function to fetch game data
def fetch_game_data(date, team1, team2):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if game['HomeTeam'] == team1 and game['AwayTeam'] == team2:
                return game
            if game['HomeTeam'] == team2 and game['AwayTeam'] == team1:
                return game
    return None

# Function to check if player scored
def check_player_score(game_id, player_name):
    url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByGame/{game_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == player_name and stat['Goals'] > 0:
                return True
    return False

# Main function to determine the outcome
def resolve_market():
    game = fetch_game_data(GAME_DATE, TEAMS["Edmonton Oilers"], TEAMS["Florida Panthers"])
    if not game:
        return "recommendation: p4"  # Game data not found or future date

    if datetime.now() < datetime.strptime(GAME_DATE + " 20:00", "%Y-%m-%d %H:%M"):
        return "recommendation: p4"  # Game has not started yet

    if game['Status'] != 'Final':
        return "recommendation: p3"  # Game not completed by the specified date

    if check_player_score(game['GameID'], PLAYER_NAME):
        return "recommendation: p2"  # Player scored
    else:
        return "recommendation: p1"  # Player did not score

# Execute the main function
if __name__ == "__main__":
    print(resolve_market())