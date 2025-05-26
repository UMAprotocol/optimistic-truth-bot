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
GAME_DATE = "2025-05-25"
PHILLIES_KEY = "PHI"
ATHLETICS_KEY = "OAK"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date_formatted}")

    if not games_today:
        # Fallback to proxy if primary fails
        games_today = make_request(PROXY_ENDPOINT, f"GamesByDate/{date_formatted}")

    if games_today:
        for game in games_today:
            if game['HomeTeam'] == PHILLIES_KEY and game['AwayTeam'] == ATHLETICS_KEY:
                if game['Status'] == 'Final':
                    home_score = game['HomeTeamRuns']
                    away_score = game['AwayTeamRuns']
                    if home_score > away_score:
                        return "recommendation: p2"  # Phillies win
                    elif away_score > home_score:
                        return "recommendation: p1"  # Athletics win
                elif game['Status'] == 'Postponed':
                    return "recommendation: p4"  # Game postponed
                elif game['Status'] == 'Canceled':
                    return "recommendation: p3"  # Game canceled
    return "recommendation: p4"  # No data or game not found

# Main execution
if __name__ == "__main__":
    result = find_game_and_determine_outcome()
    print(result)