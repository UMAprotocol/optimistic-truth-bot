import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not MLB_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": MLB_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Twins": "p2",
    "Astros": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None

def resolve_market(date_str, home_team, away_team):
    # Format the date for the API endpoint
    date_formatted = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date_formatted}"

    # Try fetching data from the proxy endpoint first
    games = get_data(f"{PROXY_ENDPOINT}/GamesByDate/{date_formatted}", HEADERS)
    if not games:
        # Fallback to the primary endpoint if proxy fails
        games = get_data(url, HEADERS)

    if games is None:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    # Check each game for the specified teams
    for game in games:
        if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
            if game["Status"] == "Final":
                home_score = game["HomeTeamRuns"]
                away_score = game["AwayTeamRuns"]
                if home_score > away_score:
                    return "recommendation: " + RESOLUTION_MAP[home_team]
                elif away_score > home_score:
                    return "recommendation: " + RESOLUTION_MAP[away_team]
            elif game["Status"] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            else:
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    # Game details
    game_date = "2025-06-13"
    home_team = "Astros"
    away_team = "Twins"

    # Resolve the market based on the game outcome
    result = resolve_market(game_date, home_team, away_team)
    print(result)