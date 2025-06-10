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
TEAM = "New York Knicks"
OPPONENT = "Indiana Pacers"

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

# Resolution map
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1"
}

def get_game_data(date, team, opponent):
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team or game['AwayTeam'] == team) and \
               (game['HomeTeam'] == opponent or game['AwayTeam'] == opponent):
                return game
    except requests.RequestException:
        try:
            # Fallback to proxy endpoint
            response = requests.get(f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{date}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if (game['HomeTeam'] == team or game['AwayTeam'] == team) and \
                   (game['HomeTeam'] == opponent or game['AwayTeam'] == opponent):
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
        return None
    return None

def resolve_market():
    game = get_game_data(GAME_DATE, TEAM, OPPONENT)
    if not game or game['Status'] != "Final":
        return RESOLUTION_MAP["No"]
    
    player_stats = get_player_stats(game['GameID'], PLAYER_NAME)
    if not player_stats or player_stats['Status'] != "Active":
        return RESOLUTION_MAP["No"]
    
    points_scored = player_stats.get('Points', 0)
    if points_scored > 30.5:
        return RESOLUTION_MAP["Yes"]
    else:
        return RESOLUTION_MAP["No"]

if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")