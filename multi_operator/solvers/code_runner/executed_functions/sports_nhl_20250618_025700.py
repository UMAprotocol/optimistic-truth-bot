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
GAME_DATE = "2025-06-17"
PLAYER_NAME = "Aleksander Barkov"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

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
        if game['Status'] == 'Final' and {game['HomeTeam'], game['AwayTeam']} == set(TEAM_ABBREVIATIONS.values()):
            player_stats_url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByDate/{GAME_DATE}/{player_name.replace(' ', '%20')}"
            response = requests.get(player_stats_url, headers=HEADERS)
            if response.status_code == 200:
                stats = response.json()
                for stat in stats:
                    if stat['Name'] == player_name and stat['Goals'] > 0.5:
                        return "p2"  # Player scored more than 0.5 goals
                return "p1"  # Player did not score more than 0.5 goals
            else:
                raise Exception(f"Failed to fetch player stats: {response.status_code} {response.text}")
    return "p3"  # Game not completed or not found

# Main function to resolve the market
def resolve_market():
    try:
        games = fetch_game_data(GAME_DATE)
        result = check_player_score(games, PLAYER_NAME)
        print(f"recommendation: {result}")
    except Exception as e:
        print(f"Error: {e}")

# Run the resolution function
if __name__ == "__main__":
    resolve_market()