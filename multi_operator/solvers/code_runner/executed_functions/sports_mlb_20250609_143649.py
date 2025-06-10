import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and API endpoints
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
    if games:
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
               (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
    return None

# Function to determine the outcome
def determine_outcome(game):
    if not game:
        return "p3"  # No game found, resolve as unknown/50-50
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return "p1" if game['HomeTeam'] == "Mumbai Indians" else "p2"
        else:
            return "p1" if game['AwayTeam'] == "Mumbai Indians" else "p2"
    elif game['Status'] == "Canceled":
        return "p3"  # Game canceled, resolve as 50-50
    else:
        return "p4"  # Game not final or canceled, cannot resolve yet

# Main execution function
def main():
    date = "2025-05-30"
    team1 = "Gujarat Titans"
    team2 = "Mumbai Indians"
    game = find_game(date, team1, team2)
    result = determine_outcome(game)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()