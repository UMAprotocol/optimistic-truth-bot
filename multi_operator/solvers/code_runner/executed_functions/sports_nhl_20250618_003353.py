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
PLAYER_NAME = "Sam Reinhart"
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
            game_id = game['GameID']
            url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByGame/{game_id}"
            response = requests.get(url, headers=HEADERS)
            if response.status_code == 200:
                player_stats = response.json()
                for stat in player_stats:
                    if stat['Name'] == player_name and stat['Goals'] > 0:
                        return True
            else:
                raise Exception(f"Failed to fetch player stats: {response.status_code} {response.text}")
    return False

# Main function to resolve the market
def resolve_market():
    try:
        games = fetch_game_data(GAME_DATE)
        if check_player_score(games, PLAYER_NAME):
            return "recommendation: p2"  # Player scored more than 0.5 goals
        else:
            return "recommendation: p1"  # Player did not score more than 0.5 goals
    except Exception as e:
        print(f"Error: {str(e)}")
        return "recommendation: p3"  # Unknown/50-50 if there is an error

# Run the main function
if __name__ == "__main__":
    result = resolve_market()
    print(result)