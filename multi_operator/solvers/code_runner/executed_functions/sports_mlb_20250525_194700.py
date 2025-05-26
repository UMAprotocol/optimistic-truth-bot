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
        if endpoint == PROXY_ENDPOINT:
            print("Proxy failed, trying primary endpoint")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to find the game and determine the outcome
def resolve_market():
    date_str = "2025-05-10"
    teams = {"Sunrisers Hyderabad": "p2", "Kolkata Knight Riders": "p1"}
    path = f"GamesByDate/{date_str}"

    games = make_request(PROXY_ENDPOINT, path)
    if games is None:
        return "recommendation: p4"  # Unable to resolve due to data fetch failure

    for game in games:
        if game['HomeTeam'] in teams and game['AwayTeam'] in teams:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return f"recommendation: {teams[game['HomeTeam']]}"
                else:
                    return f"recommendation: {teams[game['AwayTeam']]}"
            elif game['Status'] == "Canceled":
                return "recommendation: p3"
            elif game['Status'] == "Postponed":
                return "recommendation: p4"
            else:
                return "recommendation: p4"

    return "recommendation: p4"  # No matching game found or game not yet played

# Main execution
if __name__ == "__main__":
    result = resolve_market()
    print(result)