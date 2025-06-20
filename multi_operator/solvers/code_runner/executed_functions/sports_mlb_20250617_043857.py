import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Game details
GAME_DATE = "2025-06-16"
HOME_TEAM = "Athletics"
AWAY_TEAM = "Astros"

# API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb/GamesByDate/"

# Resolution map
RESOLUTION_MAP = {
    "Astros": "p2",
    "Athletics": "p1",
    "Postponed": "p4",
    "Canceled": "p3",
    "Unknown": "p3"
}

def get_games_by_date(date):
    """
    Fetch games by date from the API.
    """
    url = f"{PROXY_ENDPOINT}{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Proxy failed")
        return response.json()
    except:
        url = f"{PRIMARY_ENDPOINT}{date}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(games):
    """
    Resolve the market based on the game outcome.
    """
    for game in games:
        if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return "recommendation: " + RESOLUTION_MAP[HOME_TEAM]
                elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                    return "recommendation: " + RESOLUTION_MAP[AWAY_TEAM]
            elif game['Status'] == "Postponed":
                return "recommendation: " + RESOLUTION_MAP["Postponed"]
            elif game['Status'] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["Canceled"]
    return "recommendation: " + RESOLUTION_MAP["Unknown"]

if __name__ == "__main__":
    games = get_games_by_date(GAME_DATE)
    result = resolve_market(games)
    print(result)