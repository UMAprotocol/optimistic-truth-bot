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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Game details
GAME_DATE = "2025-06-16"
HOME_TEAM = "Rockies"
AWAY_TEAM = "Nationals"

# Resolution map
RESOLUTION_MAP = {
    "Rockies": "p2",
    "Nationals": "p1",
    "Postponed": "p4",
    "Canceled": "p3",
    "Unknown": "p3"
}

def get_game_data(date):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}"
    primary_url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Proxy failed")
    except:
        response = requests.get(primary_url, headers=HEADERS, timeout=10)
        if not response.ok:
            response.raise_for_status()

    games = response.json()
    for game in games:
        if game["HomeTeam"] == HOME_TEAM and game["AwayTeam"] == AWAY_TEAM:
            return game
    return None

def resolve_market(game):
    if not game:
        return "recommendation: p4"  # Game not found, assume in-progress or error

    status = game["Status"]
    if status == "Final":
        home_score = game["HomeTeamRuns"]
        away_score = game["AwayTeamRuns"]
        if home_score > away_score:
            return f"recommendation: {RESOLUTION_MAP[HOME_TEAM]}"
        elif away_score > home_score:
            return f"recommendation: {RESOLUTION_MAP[AWAY_TEAM]}"
    elif status in ["Postponed", "Canceled"]:
        return f"recommendation: {RESOLUTION_MAP[status]}"
    else:
        return "recommendation: p4"  # In-progress or other non-final status

    return "recommendation: p3"  # Default to unknown if no conditions met

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE)
    result = resolve_market(game_info)
    print(result)