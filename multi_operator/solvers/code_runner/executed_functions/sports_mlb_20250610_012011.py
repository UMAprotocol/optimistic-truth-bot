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
GAME_DATE = "2025-06-01"
HOME_TEAM = "Guardians"
AWAY_TEAM = "Angels"

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p1",  # Guardians win
    AWAY_TEAM: "p2",  # Angels win
    "50-50": "p3",    # Canceled or tie
    "Too early to resolve": "p4"  # Not enough data or future game
}

def get_game_data(date):
    """Fetch game data for a specific date."""
    url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
    primary_url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            response = requests.get(primary_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def analyze_game_results(games):
    """Analyze game results to determine the outcome."""
    for game in games:
        if game['Day'] == GAME_DATE and {game['HomeTeam'], game['AwayTeam']} == {HOME_TEAM, AWAY_TEAM}:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[HOME_TEAM]
                elif away_score > home_score:
                    return RESOLUTION_MAP[AWAY_TEAM]
            elif game['Status'] in ["Canceled", "Postponed"]:
                return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

def main():
    games = get_game_data(GAME_DATE)
    if games:
        recommendation = analyze_game_results(games)
    else:
        recommendation = RESOLUTION_MAP["Too early to resolve"]
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()