import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Function to make HTTP GET requests
def get_data(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return get_data(url, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to determine the outcome of the match
def determine_outcome():
    # Date and teams for the match
    match_date = "2025-06-12"
    team1 = "Aurora"
    team2 = "FURIA"

    # Fetch the schedule for the given date
    games = get_data(f"/scores/json/GamesByDate/{match_date}", use_proxy=True)
    if games is None:
        return "p3"  # Assume unknown/50-50 if data retrieval fails

    # Find the specific game
    for game in games:
        if team1 in game['HomeTeamName'] and team2 in game['AwayTeamName']:
            if game['Status'] == "Final":
                if game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "p1" if game['HomeTeamName'] == team1 else "p2"
                elif game['HomeTeamScore'] < game['AwayTeamScore']:
                    return "p2" if game['HomeTeamName'] == team1 else "p1"
                else:
                    return "p3"  # Tie
            elif game['Status'] in ["Canceled", "Postponed"]:
                return "p3"  # Game not played or completed
            else:
                return "p4"  # Game not yet completed
    return "p3"  # Game not found or other issues

# Main execution
if __name__ == "__main__":
    result = determine_outcome()
    print(f"recommendation: {result}")