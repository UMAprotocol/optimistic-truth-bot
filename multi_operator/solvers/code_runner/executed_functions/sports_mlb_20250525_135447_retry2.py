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

# Game details
GAME_DATE = "2025-05-24"
HOME_TEAM = "STL"  # St. Louis Cardinals
AWAY_TEAM = "ARI"  # Arizona Diamondbacks

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p1",  # Cardinals win
    AWAY_TEAM: "p2",  # Diamondbacks win
    "Canceled": "p3",  # Game canceled
    "Postponed": "p4",  # Game postponed
    "Unknown": "p4"    # Unknown or in-progress
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        return games
    except requests.exceptions.RequestException as e:
        print(f"Primary endpoint failed, trying proxy. Error: {e}")
        try:
            proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            return games
        except requests.exceptions.RequestException as e:
            print(f"Both primary and proxy endpoints failed. Error: {e}")
            return None

def analyze_game(games, home_team, away_team):
    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[home_team]
                elif away_score > home_score:
                    return RESOLUTION_MAP[away_team]
            elif game['Status'] in ["Canceled", "Postponed"]:
                return RESOLUTION_MAP[game['Status']]
    return RESOLUTION_MAP["Unknown"]

def main():
    games = get_game_data(GAME_DATE)
    if games:
        recommendation = analyze_game(games, HOME_TEAM, AWAY_TEAM)
        print(f"recommendation: {recommendation}")
    else:
        print("recommendation: p4")  # Unable to retrieve game data

if __name__ == "__main__":
    main()