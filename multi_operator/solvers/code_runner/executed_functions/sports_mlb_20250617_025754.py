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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to make API requests
def make_request(url, use_proxy=False):
    headers = {"Ocp-Apim-Subscription-Key": API_KEY}
    try:
        if use_proxy:
            response = requests.get(PROXY_ENDPOINT, headers=headers, timeout=10)
        else:
            response = requests.get(url, headers=headers, timeout=10)
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
def check_match_result(date):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = PRIMARY_ENDPOINT + formatted_date
    games = make_request(url)
    if games is None:
        return "p3"  # Unknown or error case

    for game in games:
        if game['HomeTeam'] == "FLA" and game['AwayTeam'] == "EST":
            home_score = game['HomeTeamRuns']
            away_score = game['AwayTeamRuns']
            total_score = home_score + away_score
            if total_score > 2.5:
                return "p2"  # Yes, more than 2.5 goals
            else:
                return "p1"  # No, not more than 2.5 goals

    return "p3"  # No matching game found

# Main execution
if __name__ == "__main__":
    match_date = "2025-06-16"
    result = check_match_result(match_date)
    print(f"recommendation: {result}")