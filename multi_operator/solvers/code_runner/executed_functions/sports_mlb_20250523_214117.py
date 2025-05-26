import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find game data
def find_game(date, team1, team2):
    games = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date}")
    if not games:
        return None
    for game in games:
        if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
           (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
            return game
    return None

# Function to determine the outcome
def determine_outcome(game):
    if not game:
        return "p4"  # Game data not found, too early to resolve
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return "p2" if game['HomeTeam'] == "RCB" else "p1"
        else:
            return "p1" if game['HomeTeam'] == "RCB" else "p2"
    elif game['Status'] == "Canceled":
        return "p3"
    elif game['Status'] == "Postponed":
        return "p4"  # Market remains open
    else:
        return "p4"  # In-progress or other statuses

# Main execution function
def main():
    date = "2025-05-13"
    team1 = "RCB"
    team2 = "SH"
    game = find_game(date, team1, team2)
    result = determine_outcome(game)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()