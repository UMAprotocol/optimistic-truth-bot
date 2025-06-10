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
TEAM1 = "STL"  # St. Louis Cardinals
TEAM2 = "TEX"  # Texas Rangers

def get_game_data(date, team1, team2):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == team1 and game['AwayTeam'] == team2:
                return game
            elif game['HomeTeam'] == team2 and game['AwayTeam'] == team1:
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if game['HomeTeam'] == team1 and game['AwayTeam'] == team2:
                    return game
                elif game['HomeTeam'] == team2 and game['AwayTeam'] == team1:
                    return game
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
    return None

def resolve_market(game):
    if not game:
        return "recommendation: p4"  # No data available
    if game['Status'] == 'Final':
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return "recommendation: p2" if game['HomeTeam'] == TEAM1 else "recommendation: p1"
        else:
            return "recommendation: p1" if game['HomeTeam'] == TEAM1 else "recommendation: p2"
    elif game['Status'] == 'Canceled':
        return "recommendation: p3"
    elif game['Status'] == 'Postponed':
        return "recommendation: p4"  # Market remains open
    return "recommendation: p4"  # In case of any other status

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE, TEAM1, TEAM2)
    result = resolve_market(game_info)
    print(result)