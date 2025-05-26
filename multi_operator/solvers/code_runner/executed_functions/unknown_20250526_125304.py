import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants for API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_MLB_API_KEY}

# Function to make API requests
def make_api_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    try:
        response = requests.get(f"{endpoint}{url}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_api_request(url, use_proxy=False)
        else:
            print(f"API request failed: {e}")
            return None

# Function to determine the outcome of the game
def determine_outcome(game_info):
    if not game_info:
        return "p4"  # No game info available
    if game_info['Status'] == 'Final':
        home_score = game_info['HomeTeamRuns']
        away_score = game_info['AwayTeamRuns']
        if home_score > away_score:
            return "p1" if game_info['HomeTeam'] == 'TEX' else "p2"
        elif away_score > home_score:
            return "p1" if game_info['AwayTeam'] == 'TEX' else "p2"
        else:
            return "p3"  # Tie
    elif game_info['Status'] in ['Canceled', 'Postponed']:
        return "p3"  # Game not played
    else:
        return "p4"  # Game not final

# Main function to process the game data
def process_game_data(date, team1, team2):
    game_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games = make_api_request(f"/GamesByDate/{game_date}", use_proxy=True)
    if games:
        for game in games:
            if {game['HomeTeam'], game['AwayTeam']} == {team1, team2}:
                return determine_outcome(game)
    return "p4"  # Default to unresolved if no game matches

# Example usage
if __name__ == "__main__":
    date = "2025-04-23"
    team1 = "TEX"  # Texas Rangers
    team2 = "OAK"  # Oakland Athletics
    recommendation = process_game_data(date, team1, team2)
    print(f"recommendation: {recommendation}")