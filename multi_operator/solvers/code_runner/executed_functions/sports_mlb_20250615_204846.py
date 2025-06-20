import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants for the game
GAME_DATE = "2025-06-15"
HOME_TEAM = "Astros"
AWAY_TEAM = "Twins"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    HOME_TEAM: "p1",  # Astros win
    AWAY_TEAM: "p2",  # Twins win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Scheduled": "p4"  # Game scheduled but not yet played
}

def get_game_data(date):
    """Fetch game data for a specific date."""
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} {response.reason}")

def resolve_market(games):
    """Resolve the market based on game data."""
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
                return RESOLUTION_MAP.get(game['Status'], "p4")
    return "p4"  # No relevant game found

if __name__ == "__main__":
    try:
        games = get_game_data(GAME_DATE)
        recommendation = resolve_market(games)
        print(f"recommendation: {recommendation}")
    except Exception as e:
        print(f"Error: {str(e)}")