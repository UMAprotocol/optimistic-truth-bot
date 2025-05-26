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
def determine_outcome(game_date, team1, team2):
    games = make_api_request(f"/GamesByDate/{game_date}")
    if games is None:
        return "recommendation: p4"  # Unable to retrieve data

    for game in games:
        if {game['HomeTeam'], game['AwayTeam']} == {team1, team2}:
            if game['Status'] == 'Final':
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                
                if winner == team1:
                    return "recommendation: p1"
                else:
                    return "recommendation: p2"
            elif game['Status'] in ['Canceled', 'Postponed']:
                return "recommendation: p3"
            else:
                return "recommendation: p4"  # Game not final

    return "recommendation: p4"  # No matching game found

# Main execution function
def main():
    # Example game details
    game_date = "2025-04-23"
    team1 = "Texas Rangers"
    team2 = "Oakland Athletics"

    result = determine_outcome(game_date, team1, team2)
    print(result)

if __name__ == "__main__":
    main()