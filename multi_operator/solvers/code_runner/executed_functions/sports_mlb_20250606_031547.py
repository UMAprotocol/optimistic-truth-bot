import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Game and player details
GAME_DATE = "2025-06-05"
PLAYER_NAME = "Tyrese Haliburton"
TEAM_ABBREVIATION = "IND"  # Indiana Pacers
OPPONENT_ABBREVIATION = "OKC"  # Oklahoma City Thunder

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error during request: {e}")
        return None

# Function to find the game ID
def find_game_id():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%b-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_formatted}"
    games = make_request(url, HEADERS)
    if games:
        for game in games:
            if game['HomeTeam'] == OPPONENT_ABBREVIATION and game['AwayTeam'] == TEAM_ABBREVIATION:
                return game['GameId']
    return None

# Function to check player's points
def check_player_points(game_id):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    player_stats = make_request(url, HEADERS)
    if player_stats:
        for stat in player_stats:
            if stat['Name'] == PLAYER_NAME:
                points = stat['Points']
                return points >= 18
    return False

# Main function to resolve the market
def resolve_market():
    game_id = find_game_id()
    if game_id:
        if check_player_points(game_id):
            return "recommendation: p2"  # Yes, scored 18+ points
        else:
            return "recommendation: p1"  # No, did not score 18+ points
    return "recommendation: p1"  # No game found or player did not play

# Run the resolution function and print the result
if __name__ == "__main__":
    result = resolve_market()
    print(result)