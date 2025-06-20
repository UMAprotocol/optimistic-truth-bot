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
    date_str = "2025-06-15"
    teams = ["Bayern Munich", "Auckland City"]
    url = f"/GamesByDate/{date_str}"

    games = make_request(url)
    if games is None:
        return "p3"  # Unknown or error case

    for game in games:
        if game['HomeTeam'] in teams and game['AwayTeam'] in teams:
            if game['Status'] == 'Final':
                total_goals = game['HomeTeamGoals'] + game['AwayTeamGoals']
                if total_goals > 4.5:
                    return "p2"  # Yes, more than 4.5 goals scored
                else:
                    return "p1"  # No, not more than 4.5 goals scored
            elif game['Status'] in ['Canceled', 'Postponed']:
                return "p1"  # No, as the match was not played or completed

    return "p3"  # If no relevant game was found

# Main execution
if __name__ == "__main__":
    result = check_match_result()
    print(f"recommendation: {result}")