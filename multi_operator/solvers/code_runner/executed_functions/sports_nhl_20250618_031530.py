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
GAME_DATE = "2025-06-17"
PLAYER_NAME = "Brad Marchand"
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

# Main function to resolve the market
def resolve_market():
    game = fetch_game_data(GAME_DATE, TEAMS["Edmonton Oilers"], TEAMS["Florida Panthers"])
    if not game:
        return "recommendation: p4"  # Game data not found or game not yet played
    if game['Status'] != "Final":
        return "recommendation: p4"  # Game not completed
    if datetime.now() > datetime(2025, 12, 31, 23, 59):
        return "recommendation: p3"  # Market resolves to 50-50 after deadline

    player_scored = check_player_score(game['GameID'], PLAYER_NAME)
    if player_scored:
        return "recommendation: p2"  # Player scored a goal
    else:
        return "recommendation: p1"  # Player did not score

# Run the main function
if __name__ == "__main__":
    result = resolve_market()
    print(result)