import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants
DATE = "2025-05-23"
TEAM1 = "Yankees"
TEAM2 = "Rockies"
RESOLUTION_MAP = {
    "Yankees": "p2",  # Yankees win
    "Rockies": "p1",  # Rockies win
    "50-50": "p3",    # Game canceled or tie
    "Too early to resolve": "p4"  # Not enough data or game not completed
}

# Function to get data from API
def get_data(url, proxy_url=None):
    try:
        response = requests.get(proxy_url if proxy_url else url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if proxy_url:
            # Try primary endpoint if proxy fails
            return get_data(url)
        print(f"Error: {e}")
        return None

# Function to determine the outcome of the game
def determine_outcome(data):
    if not data:
        return "Too early to resolve"
    for game in data:
        if game['Date'][:10] == DATE and {game['HomeTeam'], game['AwayTeam']} == {TEAM1, TEAM2}:
            if game['Status'] == 'Final':
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return game['HomeTeam']
                elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                    return game['AwayTeam']
            elif game['Status'] in ['Canceled', 'Postponed']:
                return "50-50"
    return "Too early to resolve"

# Main execution
if __name__ == "__main__":
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{DATE}"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    games_data = get_data(url, proxy_url)
    outcome = determine_outcome(games_data)
    recommendation = RESOLUTION_MAP.get(outcome, "p4")
    print(f"recommendation: {recommendation}")