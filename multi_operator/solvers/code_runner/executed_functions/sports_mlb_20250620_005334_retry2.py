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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Game details
GAME_DATE = "2025-06-19"
HOME_TEAM = "MIA"  # Miami Marlins
AWAY_TEAM = "PHI"  # Philadelphia Phillies

# Resolution map
RESOLUTION_MAP = {
    "MIA": "p1",  # Marlins win
    "PHI": "p2",  # Phillies win
    "Canceled": "p3",  # Game canceled
    "Postponed": "p4",  # Game postponed or in progress
    "Unknown": "p4"  # Unknown or no data
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        return games
    except requests.exceptions.RequestException as e:
        print(f"Primary API failed, trying proxy. Error: {e}")
        try:
            proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            return games
        except requests.exceptions.RequestException as e:
            print(f"Proxy API also failed. Error: {e}")
            return None

def analyze_game(games, home_team, away_team):
    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[home_team]
                elif away_score > home_score:
                    return RESOLUTION_MAP[away_team]
            elif game['Status'] in ["Canceled", "Postponed"]:
                return RESOLUTION_MAP[game['Status']]
    return RESOLUTION_MAP["Unknown"]

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    if games:
        recommendation = analyze_game(games, HOME_TEAM, AWAY_TEAM)
    else:
        recommendation = RESOLUTION_MAP["Unknown"]
    print(f"recommendation: {recommendation}")