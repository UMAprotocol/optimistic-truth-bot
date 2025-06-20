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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map
RESOLUTION_MAP = {
    "White Sox": "p2",
    "Rangers": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_data(url, params=None):
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            # Fallback to proxy endpoint
            proxy_url = PROXY_ENDPOINT + url[len(PRIMARY_ENDPOINT):]
            response = requests.get(proxy_url, headers=HEADERS, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

def resolve_market():
    today_date = datetime.utcnow().strftime("%Y-%m-%d")
    games_today_url = f"{PRIMARY_ENDPOINT}/GamesByDate/{today_date}"
    games = get_data(games_today_url)

    if not games:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    for game in games:
        if game["HomeTeam"] == "CHW" and game["AwayTeam"] == "TEX":
            if game["Status"] == "Final":
                home_score = game["HomeTeamRuns"]
                away_score = game["AwayTeamRuns"]
                if home_score > away_score:
                    return "recommendation: " + RESOLUTION_MAP["White Sox"]
                elif away_score > home_score:
                    return "recommendation: " + RESOLUTION_MAP["Rangers"]
            elif game["Status"] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            else:
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    result = resolve_market()
    print(result)