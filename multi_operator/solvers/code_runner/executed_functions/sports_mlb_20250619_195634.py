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
GAME_DATE = "2025-06-19"
HOME_TEAM = "CIN"  # Cincinnati Reds
AWAY_TEAM = "MIN"  # Minnesota Twins

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p1",  # Reds win
    AWAY_TEAM: "p2",  # Twins win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Scheduled": "p4",  # Game scheduled but not yet played
    "InProgress": "p4",  # Game in progress
    "Final": "p4"  # Game completed, determine winner
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        return games
    except requests.exceptions.RequestException as e:
        print(f"Error accessing primary endpoint: {e}")
        try:
            # Fallback to proxy endpoint
            proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            return games
        except requests.exceptions.RequestException as e:
            print(f"Error accessing proxy endpoint: {e}")
            return None

def resolve_game(games, home_team, away_team):
    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            status = game['Status']
            if status == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[home_team]
                elif away_score > home_score:
                    return RESOLUTION_MAP[away_team]
            return RESOLUTION_MAP.get(status, "p4")
    return "p4"

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    if games:
        recommendation = resolve_game(games, HOME_TEAM, AWAY_TEAM)
    else:
        recommendation = "p4"  # Unable to retrieve game data
    print(f"recommendation: {recommendation}")