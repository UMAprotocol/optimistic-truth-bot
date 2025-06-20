import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Game details
GAME_DATE = "2025-06-12"
HOME_TEAM = "Cubs"
AWAY_TEAM = "Pirates"

# Resolution map
RESOLUTION_MAP = {
    "Cubs": "p1",
    "Pirates": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def resolve_game(game_date, home_team, away_team):
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
    games = get_data(url, HEADERS)
    
    if games is None:
        return RESOLUTION_MAP["Too early to resolve"]
    
    for game in games:
        if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
            if game["Status"] == "Final":
                home_score = game["HomeTeamRuns"]
                away_score = game["AwayTeamRuns"]
                if home_score > away_score:
                    return RESOLUTION_MAP[home_team]
                elif away_score > home_score:
                    return RESOLUTION_MAP[away_team]
            elif game["Status"] == "Canceled":
                return RESOLUTION_MAP["50-50"]
            elif game["Status"] == "Postponed":
                return RESOLUTION_MAP["Too early to resolve"]
    
    return RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    result = resolve_game(GAME_DATE, HOME_TEAM, AWAY_TEAM)
    print(f"recommendation: {result}")