import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
GAME_DATE = "2025-06-12"
PLAYER_NAME = "Brad Marchand"
TEAM_ABBR_EDM = "EDM"
TEAM_ABBR_FLA = "FLA"

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error during API request: {e}")
        return None

# Function to check if Brad Marchand scored in the game
def check_player_score(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    game_stats = make_request(url, HEADERS)
    if game_stats:
        for stat in game_stats:
            if stat['Name'] == player_name and stat['Goals'] > 0.5:
                return True
    return False

# Function to find the game ID of the specific match
def find_game_id(date, team1, team2):
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
    games = make_request(url, HEADERS)
    if games:
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
               (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game['GameID']
    return None

# Main function to determine the outcome
def main():
    game_id = find_game_id(GAME_DATE, TEAM_ABBR_EDM, TEAM_ABBR_FLA)
    if game_id:
        if check_player_score(game_id, PLAYER_NAME):
            print("recommendation: p2")  # Brad Marchand scored more than 0.5 goals
        else:
            print("recommendation: p1")  # Brad Marchand did not score more than 0.5 goals
    else:
        print("recommendation: p4")  # Game not found or not yet played

if __name__ == "__main__":
    main()