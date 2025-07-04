import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
DATE = "2025-06-17"
TEAM1 = "Toronto Blue Jays"  # p1
TEAM2 = "Arizona Diamondbacks"  # p2
RESOLUTION_MAP = {
    "Toronto Blue Jays": "p1",
    "Arizona Diamondbacks": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_json_response(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data from {url}: {str(e)}")
        return None

def find_game(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{formatted_date}"
    games = get_json_response(url)
    if games is None:
        return None, "Too early to resolve"
    
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            return game, game["Status"]
    return None, "Too early to resolve"

def resolve_market(game, status):
    if status in ["Final"]:
        home_runs = game["HomeTeamRuns"]
        away_runs = game["AwayTeamRuns"]
        if home_runs > away_runs:
            return RESOLUTION_MAP[game["HomeTeam"]]
        elif away_runs > home_runs:
            return RESOLUTION_MAP[game["AwayTeam"]]
    elif status in ["Canceled"]:
        return RESOLUTION_MAP["50-50"]
    elif status in ["Postponed"]:
        return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    game, status = find_game(DATE, TEAM1, TEAM2)
    if game:
        recommendation = resolve_market(game, status)
    else:
        recommendation = RESOLUTION_MAP["Too early to resolve"]
    print(f"recommendation: {recommendation}")