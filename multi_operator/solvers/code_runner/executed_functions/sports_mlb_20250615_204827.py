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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-mlb-proxy"

# Game details
GAME_DATE = "2025-06-15"
HOME_TEAM = "Astros"
AWAY_TEAM = "Twins"

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p1",
    AWAY_TEAM: "p2",
    "Postponed": "p4",
    "Canceled": "p3",
    "Scheduled": "p4"
}

def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def resolve_game_status(games):
    for game in games:
        if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[HOME_TEAM]
                elif away_score > home_score:
                    return RESOLUTION_MAP[AWAY_TEAM]
            else:
                return RESOLUTION_MAP[game['Status']]
    return "p4"

def main():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PROXY_ENDPOINT}/GamesByDate/{date_formatted}"
    games = get_data(url, HEADERS)
    if not games:
        print("Proxy failed, trying primary endpoint...")
        url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date_formatted}"
        games = get_data(url, HEADERS)
    
    if games:
        recommendation = resolve_game_status(games)
        print(f"recommendation: {recommendation}")
    else:
        print("recommendation: p4")

if __name__ == "__main__":
    main()