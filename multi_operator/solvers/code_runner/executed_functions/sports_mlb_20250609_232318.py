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
GAME_DATE = "2025-06-01"
HOME_TEAM = "Rockies"
AWAY_TEAM = "Mets"

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p2",  # Rockies win
    AWAY_TEAM: "p1",  # Mets win
    "Canceled": "p3",  # Game canceled
    "Postponed": "p4",  # Game postponed
    "Unknown": "p4"   # Unknown or not enough data
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/mlb/GamesByDate/{date}", timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
                    return game
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
    return None

def resolve_market(game):
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Unknown"]
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return "recommendation: " + RESOLUTION_MAP[HOME_TEAM]
        elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
            return "recommendation: " + RESOLUTION_MAP[AWAY_TEAM]
    elif game['Status'] == "Canceled":
        return "recommendation: " + RESOLUTION_MAP["Canceled"]
    elif game['Status'] == "Postponed":
        return "recommendation: " + RESOLUTION_MAP["Postponed"]
    return "recommendation: " + RESOLUTION_MAP["Unknown"]

if __name__ == "__main__":
    game_date_str = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    game_info = get_game_data(game_date_str)
    result = resolve_market(game_info)
    print(result)