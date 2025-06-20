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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb/scores/json"

# Game details
GAME_DATE = "2025-06-18"
HOME_TEAM = "LAD"  # Los Angeles Dodgers
AWAY_TEAM = "SD"   # San Diego Padres

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p1",  # Dodgers win
    AWAY_TEAM: "p2",  # Padres win
    "50-50": "p3",    # Canceled or tie
    "Too early": "p4" # Not enough data or in progress
}

def get_games_by_date(date):
    """Fetch games by date from the API."""
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

def resolve_market(games):
    """Resolve the market based on game results."""
    for game in games:
        if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[HOME_TEAM]
                elif away_score > home_score:
                    return RESOLUTION_MAP[AWAY_TEAM]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["50-50"]
            elif game['Status'] == "Postponed":
                return RESOLUTION_MAP["Too early"]
    return RESOLUTION_MAP["Too early"]

if __name__ == "__main__":
    games = get_games_by_date(GAME_DATE)
    if games:
        recommendation = resolve_market(games)
    else:
        recommendation = RESOLUTION_MAP["Too early"]
    print(f"recommendation: {recommendation}")