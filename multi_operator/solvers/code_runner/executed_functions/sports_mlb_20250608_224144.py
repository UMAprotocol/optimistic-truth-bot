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

# Date and teams for the game
GAME_DATE = "2025-06-08"
TEAM1 = "BAL"  # Baltimore Orioles
TEAM2 = "OAK"  # Oakland Athletics

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

# Function to determine the outcome of the game
def determine_outcome(games):
    for game in games:
        if game['HomeTeam'] == TEAM1 and game['AwayTeam'] == TEAM2:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return "recommendation: p2"  # Orioles win
                elif away_score > home_score:
                    return "recommendation: p1"  # Athletics win
            elif game['Status'] == "Canceled":
                return "recommendation: p3"  # Game canceled
            elif game['Status'] == "Postponed":
                return "recommendation: p4"  # Game postponed
    return "recommendation: p4"  # No game found or in progress

# Main function to run the program
def main():
    games = make_api_request(GAME_DATE)
    if games:
        result = determine_outcome(games)
        print(result)
    else:
        print("No data available.")

if __name__ == "__main__":
    main()