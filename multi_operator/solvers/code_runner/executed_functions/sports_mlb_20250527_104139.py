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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Resolution map
RESOLUTION_MAP = {
    "Rays": "p2",
    "Twins": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error accessing primary endpoint: {e}")
        try:
            # Fallback to proxy endpoint
            proxy_url = url.replace(PRIMARY_ENDPOINT, PROXY_ENDPOINT)
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error accessing proxy endpoint: {e}")
            return None

def resolve_market(date_str):
    games_url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date_str}"
    games_data = get_data(games_url)
    if not games_data:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    for game in games_data:
        if game["HomeTeam"] == "TB" and game["AwayTeam"] == "MIN":
            if game["Status"] == "Final":
                home_score = game["HomeTeamRuns"]
                away_score = game["AwayTeamRuns"]
                if home_score > away_score:
                    return "recommendation: " + RESOLUTION_MAP["Rays"]
                elif away_score > home_score:
                    return "recommendation: " + RESOLUTION_MAP["Twins"]
            elif game["Status"] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            elif game["Status"] == "Postponed":
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    game_date = "2025-05-26"
    print(resolve_market(game_date))