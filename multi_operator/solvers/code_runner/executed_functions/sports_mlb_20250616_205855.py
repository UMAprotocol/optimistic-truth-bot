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
def make_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(url, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to check the match result
def check_match_result():
    match_date = "2025-06-16"
    teams = ["Chelsea", "LAFC"]
    games_today = make_request(f"/GamesByDate/{match_date}")

    if games_today is None:
        return "p3"  # Unknown or error

    for game in games_today:
        if game['HomeTeam'] in teams and game['AwayTeam'] in teams:
            if game['Status'] == 'Final':
                total_goals = game['HomeTeamGoals'] + game['AwayTeamGoals']
                return "p2" if total_goals > 3.5 else "p1"
            elif game['Status'] in ['Canceled', 'Postponed']:
                return "p1"
            else:
                return "p4"  # Game not completed yet

    return "p4"  # No matching game found or game not yet started

# Main execution
if __name__ == "__main__":
    result = check_match_result()
    print(f"recommendation: {result}")