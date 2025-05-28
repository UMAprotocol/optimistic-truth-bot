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
GAME_DATE = "2025-05-25"
TEAM1 = "PHI"  # Philadelphia Phillies
TEAM2 = "OAK"  # Oakland Athletics

def get_data(url, params=None):
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def check_game_status(game_date, team1, team2):
    date_formatted = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date_formatted}"
    games = get_data(games_url)

    if games is None:
        return "p4"  # Unable to fetch data, assume in-progress

    for game in games:
        if game['HomeTeam'] == team1 and game['AwayTeam'] == team2:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return "p2"  # Home team (Phillies) wins
                else:
                    return "p1"  # Away team (Athletics) wins
            elif game['Status'] == "Canceled":
                return "p3"  # Game canceled, resolve 50-50
            elif game['Status'] == "Postponed":
                return "p4"  # Game postponed, check later
    return "p4"  # No game found or not yet started

if __name__ == "__main__":
    result = check_game_status(GAME_DATE, TEAM1, TEAM2)
    print(f"recommendation: {result}")