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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Game details
GAME_DATE = "2025-05-28"
HOME_TEAM = "Mariners"
AWAY_TEAM = "Nationals"

# Resolution map
RESOLUTION_MAP = {
    "Mariners": "p1",
    "Nationals": "p2",
    "Postponed": "p4",
    "Canceled": "p3",
    "Unknown": "p3"
}

def fetch_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
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
            elif game['Status'] in ["Postponed", "Canceled"]:
                return RESOLUTION_MAP[game['Status']]
    return RESOLUTION_MAP["Unknown"]

def main():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date_formatted}"
    games = fetch_data(url)
    if games is None:
        print("Attempting to fetch data from proxy endpoint...")
        proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{date_formatted}"
        games = fetch_data(proxy_url)
        if games is None:
            return "recommendation: p4"  # Unable to fetch data from both endpoints

    recommendation = resolve_game_status(games)
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()