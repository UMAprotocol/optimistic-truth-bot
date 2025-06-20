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
GAME_DATE = "2025-06-17"
PHILLIES_KEY = "PHI"
MARLINS_KEY = "MIA"

# Resolution map
RESOLUTION_MAP = {
    "Phillies": "p2",
    "Marlins": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
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
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", timeout=10)
            response.raise_for_status()
            games = response.json()
            return games
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

def analyze_game(games):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {PHILLIES_KEY, MARLINS_KEY}:
            if game["Status"] == "Final":
                home_team_wins = game["HomeTeamRuns"] > game["AwayTeamRuns"]
                away_team_wins = game["AwayTeamRuns"] > game["HomeTeamRuns"]
                if home_team_wins:
                    return RESOLUTION_MAP["Phillies"] if game["HomeTeam"] == PHILLIES_KEY else RESOLUTION_MAP["Marlins"]
                elif away_team_wins:
                    return RESOLUTION_MAP["Marlins"] if game["AwayTeam"] == MARLINS_KEY else RESOLUTION_MAP["Phillies"]
            elif game["Status"] == "Canceled":
                return RESOLUTION_MAP["50-50"]
            elif game["Status"] == "Postponed":
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    if games:
        recommendation = analyze_game(games)
    else:
        recommendation = RESOLUTION_MAP["Too early to resolve"]
    print(f"recommendation: {recommendation}")