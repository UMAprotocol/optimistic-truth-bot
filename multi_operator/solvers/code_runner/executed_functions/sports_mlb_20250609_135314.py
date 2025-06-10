import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
GAME_DATE = "2025-05-29"
PLAYER_NAME = "Jalen Brunson"
TEAM_NAME = "New York Knicks"
OPPONENT_TEAM = "Indiana Pacers"

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Function to make API requests
def make_request(url, headers, tag="API Request"):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"{tag} - HTTP Error: {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"{tag} - Connection Error: {e}")
    except requests.exceptions.Timeout as e:
        print(f"{tag} - Timeout Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"{tag} - Error: {e}")
    return None

# Function to find the game ID
def find_game_id(date, team_name, opponent_team):
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
    games = make_request(url, HEADERS, "Find Game")
    if games:
        for game in games:
            if (game['HomeTeam'] == team_name or game['AwayTeam'] == team_name) and \
               (game['HomeTeam'] == opponent_team or game['AwayTeam'] == opponent_team):
                return game['GameId']
    return None

# Function to check player's points
def check_player_points(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    player_stats = make_request(url, HEADERS, "Player Stats")
    if player_stats:
        for stat in player_stats:
            if stat['Name'] == player_name:
                points = stat.get('Points', 0)
                return points >= 31
    return False

# Main function to resolve the market
def resolve_market():
    game_id = find_game_id(GAME_DATE, TEAM_NAME, OPPONENT_TEAM)
    if game_id:
        if check_player_points(game_id, PLAYER_NAME):
            return "recommendation: p2"  # Yes, scored 31+ points
        else:
            return "recommendation: p1"  # No, did not score 31+ points
    return "recommendation: p1"  # No game found or player did not play

# Run the resolution
if __name__ == "__main__":
    result = resolve_market()
    print(result)