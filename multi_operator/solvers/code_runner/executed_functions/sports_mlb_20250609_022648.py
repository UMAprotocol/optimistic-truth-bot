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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

# Constants
GAME_DATE = "2025-06-08"
PLAYER_NAME = "Tyrese Haliburton"
TEAM_ABBREVIATION = "IND"  # Indiana Pacers
OPPONENT_ABBREVIATION = "OKC"  # Oklahoma City Thunder
POINTS_THRESHOLD = 16.5

# Resolution map
RESOLUTION_MAP = {
    "yes": "p2",
    "no": "p1",
    "unknown": "p3"
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == TEAM_ABBREVIATION and game['AwayTeam'] == OPPONENT_ABBREVIATION:
                return game
            if game['HomeTeam'] == OPPONENT_ABBREVIATION and game['AwayTeam'] == TEAM_ABBREVIATION:
                return game
    except requests.RequestException:
        try:
            # Fallback to proxy endpoint
            response = requests.get(f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{date}", timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if game['HomeTeam'] == TEAM_ABBREVIATION and game['AwayTeam'] == OPPONENT_ABBREVIATION:
                    return game
                if game['HomeTeam'] == OPPONENT_ABBREVIATION and game['AwayTeam'] == TEAM_ABBREVIATION:
                    return game
        except requests.RequestException:
            return None
    return None

def get_player_stats(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        stats = response.json()
        for stat in stats:
            if stat['Name'] == player_name:
                return stat
    except requests.RequestException:
        try:
            # Fallback to proxy endpoint
            response = requests.get(f"{PROXY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}", timeout=10)
            response.raise_for_status()
            stats = response.json()
            for stat in stats:
                if stat['Name'] == player_name:
                    return stat
        except requests.RequestException:
            return None
    return None

def resolve_market():
    game = get_game_data(GAME_DATE)
    if not game:
        return RESOLUTION_MAP["unknown"]
    if game['Status'] != "Final":
        return RESOLUTION_MAP["no"]
    
    player_stats = get_player_stats(game['GameID'], PLAYER_NAME)
    if not player_stats:
        return RESOLUTION_MAP["no"]
    
    points_scored = player_stats.get('Points', 0)
    if points_scored > POINTS_THRESHOLD:
        return RESOLUTION_MAP["yes"]
    else:
        return RESOLUTION_MAP["no"]

# Main execution
if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")