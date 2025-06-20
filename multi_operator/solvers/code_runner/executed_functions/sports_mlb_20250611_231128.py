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
GAME_DATE = "2025-06-11"
HOME_TEAM = "Los Angeles Dodgers"
AWAY_TEAM = "San Diego Padres"

# API URLs
BASE_URL = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"

def get_game_data(date):
    """Fetch game data for a specific date."""
    url = f"{BASE_URL}{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def analyze_game(games):
    """Analyze game data to determine the outcome."""
    for game in games:
        if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return "recommendation: p2"  # Dodgers win
                elif away_score > home_score:
                    return "recommendation: p1"  # Padres win
            elif game['Status'] == "Postponed":
                return "recommendation: p4"  # Game postponed
            elif game['Status'] == "Canceled":
                return "recommendation: p3"  # Game canceled
    return "recommendation: p4"  # No game found or in progress

def main():
    try:
        games = get_game_data(GAME_DATE)
        result = analyze_game(games)
        print(result)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()