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
TEAMS = ["EDM", "FLA"]  # Edmonton Oilers and Florida Panthers

# Function to fetch game data
def fetch_game_data(date):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} {response.text}")

# Function to check if player scored
def check_player_score(games, player_name):
    for game in games:
        if game['HomeTeam'] in TEAMS and game['AwayTeam'] in TEAMS:
            if game['Status'] == "Final":
                for player in game['PlayerGames']:
                    if player['Name'] == player_name and player['Goals'] > 0:
                        return True
    return False

# Main function to resolve the market
def resolve_market():
    try:
        games = fetch_game_data(GAME_DATE)
        player_scored = check_player_score(games, PLAYER_NAME)
        if player_scored:
            return "recommendation: p2"  # Player scored more than 0.5 goals
        else:
            return "recommendation: p1"  # Player did not score more than 0.5 goals
    except Exception as e:
        print(f"Error: {str(e)}")
        return "recommendation: p3"  # Unknown/50-50 if there's an error

# Execute the main function
if __name__ == "__main__":
    result = resolve_market()
    print(result)