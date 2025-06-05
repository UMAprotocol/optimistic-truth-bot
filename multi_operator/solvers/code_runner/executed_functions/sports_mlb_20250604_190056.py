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

# Game details
GAME_DATE = "2025-05-31"
TEAM1 = "ARI"  # Arizona Diamondbacks
TEAM2 = "WAS"  # Washington Nationals

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}/{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome():
    # Convert game date to datetime object
    game_datetime = datetime.strptime(GAME_DATE, "%Y-%m-%d")
    formatted_date = game_datetime.strftime("%Y-%m-%d")

    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, f"GamesByDate/{formatted_date}")
    if games is None:
        # Fallback to primary endpoint
        games = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{formatted_date}")

    if games:
        for game in games:
            if game['HomeTeam'] == TEAM1 and game['AwayTeam'] == TEAM2 or \
               game['HomeTeam'] == TEAM2 and game['AwayTeam'] == TEAM1:
                if game['Status'] == "Final":
                    home_score = game['HomeTeamRuns']
                    away_score = game['AwayTeamRuns']
                    if home_score > away_score:
                        winner = game['HomeTeam']
                    else:
                        winner = game['AwayTeam']
                    if winner == TEAM1:
                        return "recommendation: p1"
                    else:
                        return "recommendation: p2"
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"
    return "recommendation: p4"

# Main execution
if __name__ == "__main__":
    result = find_game_and_determine_outcome()
    print(result)