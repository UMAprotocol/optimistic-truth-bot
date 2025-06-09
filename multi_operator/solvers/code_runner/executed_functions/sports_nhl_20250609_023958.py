import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers and API endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Function to make API requests
def make_api_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint...")
            return make_api_request(url, use_proxy=False)
        else:
            print(f"API request failed: {e}")
            return None

# Function to find the game and determine the outcome
def resolve_market():
    date_str = "2025-06-08"
    teams = {"Pacers": "IND", "Thunder": "OKC"}
    games_today = make_api_request(f"/GamesByDate/{date_str}", use_proxy=True)

    if not games_today:
        return "recommendation: p4"  # Unable to retrieve data

    for game in games_today:
        if {game["HomeTeam"], game["AwayTeam"]} == set(teams.values()):
            if game["Status"] == "Final":
                if game["HomeTeam"] == teams["Pacers"] and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return "recommendation: p2"
                elif game["AwayTeam"] == teams["Pacers"] and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return "recommendation: p2"
                else:
                    return "recommendation: p1"
            elif game["Status"] == "Postponed":
                return "recommendation: p4"  # Market remains open
            elif game["Status"] == "Canceled":
                return "recommendation: p3"  # Resolve 50-50
    return "recommendation: p4"  # Game not found or in progress

# Main execution
if __name__ == "__main__":
    result = resolve_market()
    print(result)