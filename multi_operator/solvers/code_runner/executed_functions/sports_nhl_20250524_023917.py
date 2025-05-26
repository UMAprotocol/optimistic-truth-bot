import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Constants
DATE = "2025-05-23"
TEAM1 = "IND"  # Indiana Pacers
TEAM2 = "NY"   # New York Knicks
RESOLUTION_MAP = {
    TEAM1: "p2",  # Pacers win
    TEAM2: "p1",  # Knicks win
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/nba/GamesByDate/"

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_games_by_date(date):
    url = f"{PROXY_ENDPOINT}{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Proxy failed")
        return response.json()
    except:
        url = f"{PRIMARY_ENDPOINT}{date}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()

def analyze_game_results(games):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
            if game["Status"] == "Final":
                home_team_wins = game["HomeTeamScore"] > game["AwayTeamScore"]
                winner = game["HomeTeam"] if home_team_wins else game["AwayTeam"]
                return RESOLUTION_MAP[winner]
            elif game["Status"] in ["Canceled", "Postponed"]:
                return RESOLUTION_MAP["50-50"]
            else:
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

def main():
    date_str = datetime.strptime(DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    games = get_games_by_date(date_str)
    recommendation = analyze_game_results(games)
    print("recommendation:", recommendation)

if __name__ == "__main__":
    main()