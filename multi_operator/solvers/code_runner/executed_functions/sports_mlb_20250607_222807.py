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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb/scores/json"

# Game details
GAME_DATE = "2025-06-07"
HOME_TEAM = "Nationals"
AWAY_TEAM = "Rangers"

# Function to make API requests
def make_api_request(endpoint, path):
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
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_api_request(PROXY_ENDPOINT, f"GamesByDate/{date_formatted}")
    if not games_today:
        games_today = make_api_request(PRIMARY_ENDPOINT, f"GamesByDate/{date_formatted}")

    if games_today:
        for game in games_today:
            if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
                if game['Status'] == 'Final':
                    home_score = game['HomeTeamRuns']
                    away_score = game['AwayTeamRuns']
                    if home_score > away_score:
                        return "recommendation: p1"  # Home team wins
                    elif away_score > home_score:
                        return "recommendation: p2"  # Away team wins
                elif game['Status'] == 'Postponed':
                    return "recommendation: p4"  # Game postponed
                elif game['Status'] == 'Canceled':
                    return "recommendation: p3"  # Game canceled
    return "recommendation: p4"  # No data or game not found

# Main execution
if __name__ == "__main__":
    result = find_game_and_determine_outcome()
    print(result)