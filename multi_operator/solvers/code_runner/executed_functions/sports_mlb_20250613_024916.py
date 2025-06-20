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
GAME_DATE = "2025-06-12"
HOME_TEAM = "HOU"  # Houston Astros
AWAY_TEAM = "CWS"  # Chicago White Sox

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p1",  # Astros win
    AWAY_TEAM: "p2",  # White Sox win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Scheduled": "p4",  # Game not yet played
    "InProgress": "p4",  # Game in progress
    "Final": None  # Final (determine winner)
}

def get_game_data(date):
    """Fetch game data for a specific date."""
    url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if not response.ok:
        # Fallback to primary endpoint if proxy fails
        url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
        response = requests.get(url, headers=HEADERS)
        if not response.ok:
            raise Exception(f"Failed to fetch data: {response.status_code} {response.text}")
    return response.json()

def determine_outcome(games):
    """Determine the outcome of the game based on the game data."""
    for game in games:
        if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
            status = game['Status']
            if status == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[HOME_TEAM]
                elif away_score > home_score:
                    return RESOLUTION_MAP[AWAY_TEAM]
            else:
                return RESOLUTION_MAP.get(status, "p4")
    return "p4"  # No relevant game found

if __name__ == "__main__":
    try:
        games = get_game_data(GAME_DATE)
        result = determine_outcome(games)
        print(f"recommendation: {result}")
    except Exception as e:
        print(f"Error: {str(e)}")