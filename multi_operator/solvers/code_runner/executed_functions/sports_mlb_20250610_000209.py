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

# Game details
GAME_DATE = "2025-06-01"
HOME_TEAM = "Astros"
AWAY_TEAM = "Rays"

# API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata/mlb/GamesByDate/"

# Function to make API requests
def make_api_request(date):
    url = f"{PRIMARY_ENDPOINT}{date}"
    proxy_url = f"{PROXY_ENDPOINT}{date}"
    try:
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        if not response.ok:
            response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return None

# Function to determine the game outcome
def determine_outcome(games):
    for game in games:
        if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return "recommendation: p1"  # Astros win
                elif away_score > home_score:
                    return "recommendation: p2"  # Rays win
            elif game['Status'] == "Canceled":
                return "recommendation: p3"  # Game canceled
            elif game['Status'] == "Postponed":
                # Check for rescheduled date
                new_date = game['Day']
                if new_date > GAME_DATE:
                    return "recommendation: p4"  # Game postponed, check later
    return "recommendation: p4"  # No game found or in progress

# Main function to run the program
if __name__ == "__main__":
    games = make_api_request(GAME_DATE)
    if games:
        result = determine_outcome(games)
        print(result)
    else:
        print("No data available.")