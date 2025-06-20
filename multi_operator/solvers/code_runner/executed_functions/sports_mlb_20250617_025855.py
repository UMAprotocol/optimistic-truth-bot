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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map for outcomes
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "Unknown": "p3"
}

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check the match and calculate goals
def check_match_and_goals():
    date_str = "2025-06-16"
    teams = ["Flamengo", "Esperance Sportive de Tunis"]
    path = f"GamesByDate/{date_str}"

    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, path)
    if not games:
        # Fallback to primary endpoint if proxy fails
        games = make_request(PRIMARY_ENDPOINT, path)

    if games is None:
        return "p3"  # Unknown if no data could be retrieved

    # Find the specific game
    for game in games:
        if game['HomeTeamName'] in teams and game['AwayTeamName'] in teams:
            home_goals = game['HomeTeamScore']
            away_goals = game['AwayTeamScore']
            total_goals = home_goals + away_goals
            if total_goals > 2.5:
                return RESOLUTION_MAP["Yes"]
            else:
                return RESOLUTION_MAP["No"]

    # If no matching game is found
    return "p3"  # Unknown

# Main execution
if __name__ == "__main__":
    result = check_match_and_goals()
    print(f"recommendation: {result}")