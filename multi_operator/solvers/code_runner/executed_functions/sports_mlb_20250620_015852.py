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

# Resolution map
RESOLUTION_MAP = {
    "Mets": "p2",
    "Braves": "p1",
    "Postponed": "p4",
    "Canceled": "p3"
}

def get_game_data(date, team1, team2):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
               (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error accessing primary endpoint: {e}")
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
                   (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                    return game
        except requests.exceptions.RequestException:
            print("Error accessing proxy endpoint.")
    return None

def resolve_market(game):
    if not game:
        return "recommendation: p4"
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        return f"recommendation: {RESOLUTION_MAP[winner]}"
    elif game['Status'] == "Postponed":
        return "recommendation: p4"
    elif game['Status'] == "Canceled":
        return "recommendation: p3"
    return "recommendation: p4"

if __name__ == "__main__":
    game_date = "2025-06-19"
    team1 = "Mets"
    team2 = "Braves"
    game = get_game_data(game_date, team1, team2)
    result = resolve_market(game)
    print(result)