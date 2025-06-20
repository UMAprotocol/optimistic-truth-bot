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

# Date and teams for the query
GAME_DATE = "2025-06-11"
HOME_TEAM = "Dodgers"
AWAY_TEAM = "Padres"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Dodgers": "p2",  # Dodgers win
    "Padres": "p1",   # Padres win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Unknown": "p4"   # Unknown or in-progress
}

def get_game_data(date):
    """Fetch game data for a specific date."""
    url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            # Fallback to primary endpoint if proxy fails
            url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
            response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def analyze_game_data(games):
    """Analyze game data to determine the outcome."""
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
    games = get_game_data(GAME_DATE)
    if games:
        result = analyze_game_data(games)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p4")  # Unable to resolve due to data fetch issue

if __name__ == "__main__":
    main()