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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{PROXY_ENDPOINT}/{path}", headers=HEADERS, timeout=10)
        if not response.ok:
            response = requests.get(f"{PRIMARY_ENDPOINT}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to find the game and determine the outcome
def resolve_game(date, team1, team2):
    games = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date}")
    if not games:
        return "p4"  # Unable to fetch data

    for game in games:
        if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
           (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return "p1" if game['HomeTeam'] == team1 else "p2"
                else:
                    return "p2" if game['HomeTeam'] == team1 else "p1"
            elif game['Status'] == "Canceled":
                return "p3"
            elif game['Status'] == "Postponed":
                # Check if the game is rescheduled within the season
                return "p4"  # Game postponed, check later
    return "p4"  # No matching game found or game not yet played

# Main function to run the resolver
if __name__ == "__main__":
    # Game details
    date = "2025-06-19"
    team1 = "Houston Astros"
    team2 = "Oakland Athletics"

    # Resolve the game outcome
    result = resolve_game(date, team1, team2)
    print(f"recommendation: {result}")