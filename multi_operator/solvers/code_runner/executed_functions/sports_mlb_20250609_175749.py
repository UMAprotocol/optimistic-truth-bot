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
GAME_DATE = "2025-05-31"
TEAM1 = "DET"  # Detroit Tigers
TEAM2 = "KCR"  # Kansas City Royals

# Resolution map
RESOLUTION_MAP = {
    TEAM1: "p2",  # Detroit Tigers win
    TEAM2: "p1",  # Kansas City Royals win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Scheduled": "p4",  # Game scheduled but not yet played
    "In Progress": "p4",  # Game in progress
    "Final": None  # Final but need to check who won
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == TEAM2 and game['AwayTeam'] == TEAM1:
                return game
            elif game['HomeTeam'] == TEAM1 and game['AwayTeam'] == TEAM2:
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if game['HomeTeam'] == TEAM2 and game['AwayTeam'] == TEAM1:
                    return game
                elif game['HomeTeam'] == TEAM1 and game['AwayTeam'] == TEAM2:
                    return game
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
    return None

def resolve_market(game):
    if game is None:
        return "p4"  # No data available
    status = game['Status']
    if status == "Final":
        home_runs = game['HomeTeamRuns']
        away_runs = game['AwayTeamRuns']
        if home_runs > away_runs:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        return RESOLUTION_MAP.get(winner, "p3")  # Default to 50-50 if something unexpected
    else:
        return RESOLUTION_MAP.get(status, "p4")  # Default to too early if status not recognized

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE)
    recommendation = resolve_market(game_info)
    print(f"recommendation: {recommendation}")