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
GAME_DATE = "2025-06-01"
HOME_TEAM = "Red Sox"
AWAY_TEAM = "Braves"

# Resolution map
RESOLUTION_MAP = {
    "Red Sox": "p2",  # Home team wins
    "Braves": "p1",   # Away team wins
    "50-50": "p3",    # Game canceled or postponed without resolution
    "Too early to resolve": "p4"  # Not enough data or game not yet played
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        return games
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            # Fallback to proxy endpoint
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            return games
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

def resolve_market(games, home_team, away_team):
    if games is None:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return "recommendation: " + RESOLUTION_MAP[home_team]
                elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                    return "recommendation: " + RESOLUTION_MAP[away_team]
            elif game['Status'] in ["Canceled", "Postponed"]:
                return "recommendation: " + RESOLUTION_MAP["50-50"]

    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    result = resolve_market(games, HOME_TEAM, AWAY_TEAM)
    print(result)