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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Game details
GAME_DATE = "2025-05-27"
HOME_TEAM = "Astros"
AWAY_TEAM = "Athletics"

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p1",
    AWAY_TEAM: "p2",
    "Canceled": "p3",
    "Postponed": "p4",
    "In Progress": "p4"
}

def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def resolve_market(game_date, home_team, away_team):
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
    games = get_data(url, HEADERS)
    
    if games:
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                if game['Status'] == "Final":
                    home_score = game['HomeTeamRuns']
                    away_score = game['AwayTeamRuns']
                    if home_score > away_score:
                        return "recommendation: " + RESOLUTION_MAP[home_team]
                    elif away_score > home_score:
                        return "recommendation: " + RESOLUTION_MAP[away_team]
                else:
                    return "recommendation: " + RESOLUTION_MAP[game['Status']]
    return "recommendation: p4"

if __name__ == "__main__":
    result = resolve_market(GAME_DATE, HOME_TEAM, AWAY_TEAM)
    print(result)