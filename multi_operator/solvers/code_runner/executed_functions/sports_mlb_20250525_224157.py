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
GAME_DATE = "2025-05-25"
HOME_TEAM = "San Diego Padres"
AWAY_TEAM = "Atlanta Braves"

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p2",  # Padres win
    AWAY_TEAM: "p1",  # Braves win
    "Canceled": "p3",  # Game canceled
    "Postponed": "p4",  # Game postponed
    "Scheduled": "p4"  # Game scheduled/not yet played
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        return games
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            # Fallback to proxy endpoint
            response = requests.get(PROXY_ENDPOINT, headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            return games
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

def resolve_market(games):
    for game in games:
        if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return "recommendation: " + RESOLUTION_MAP[HOME_TEAM]
                elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                    return "recommendation: " + RESOLUTION_MAP[AWAY_TEAM]
            elif game['Status'] in ["Canceled", "Postponed"]:
                return "recommendation: " + RESOLUTION_MAP[game['Status']]
    return "recommendation: " + RESOLUTION_MAP["Scheduled"]

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    if games:
        result = resolve_market(games)
        print(result)
    else:
        print("recommendation: p4")  # Unable to resolve due to data fetch failure