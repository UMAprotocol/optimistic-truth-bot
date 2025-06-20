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
PLAYER_NAME = "Aleksander Barkov"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Function to fetch game data
def fetch_game_data(date):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS, timeout=10)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

# Function to check player's goal in the game
def check_player_goal(games, player_name):
    for game in games:
        if game['Status'] == "Final" and {game['HomeTeam'], game['AwayTeam']} == set(TEAM_ABBREVIATIONS.values()):
            game_id = game['GameID']
            url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByGame/{game_id}"
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                player_stats = response.json()
                for stat in player_stats:
                    if stat['Name'] == player_name and stat['Goals'] > 0.5:
                        return "p2"  # Player scored more than 0.5 goals
                return "p1"  # Player did not score more than 0.5 goals
            else:
                response.raise_for_status()
    return "p3"  # Game not found or not completed

# Main execution function
def main():
    try:
        games = fetch_game_data(GAME_DATE)
        result = check_player_goal(games, PLAYER_NAME)
        print(f"recommendation: {result}")
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    main()