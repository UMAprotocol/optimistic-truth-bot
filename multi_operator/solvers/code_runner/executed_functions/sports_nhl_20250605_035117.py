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

# NHL game and player details
GAME_DATE = "2025-06-04"
TEAM_ABBR_FLORIDA = "FLA"
TEAM_ABBR_EDMONTON = "EDM"
PLAYER_NAME = "Matthew Tkachuk"

# Function to fetch game data
def fetch_game_data(date, team1, team2):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
               (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
    return None

# Function to check if player scored
def check_player_score(game_id, player_name):
    url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByGame/{game_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == player_name and stat['Goals'] >= 1:
                return True
    return False

# Main function to determine the outcome
def main():
    game = fetch_game_data(GAME_DATE, TEAM_ABBR_FLORIDA, TEAM_ABBR_EDMONTON)
    if game and game['Status'] == "Final":
        player_scored = check_player_score(game['GameID'], PLAYER_NAME)
        if player_scored:
            print("recommendation: p2")  # Player scored 1+ goals
        else:
            print("recommendation: p1")  # Player did not score
    else:
        print("recommendation: p1")  # Game not completed or player did not play

if __name__ == "__main__":
    main()