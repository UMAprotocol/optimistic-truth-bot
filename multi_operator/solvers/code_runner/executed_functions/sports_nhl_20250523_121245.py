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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-nba-proxy/GamesByDate/"
DATE = "2025-05-22"
TEAMS = {"Minnesota Timberwolves": "p2", "Oklahoma City Thunder": "p1"}
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Function to fetch game data
def fetch_game_data(date):
    url = f"{PRIMARY_ENDPOINT}{date}"
    proxy_url = f"{PROXY_ENDPOINT}{date}"
    try:
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Proxy failed")
        return response.json()
    except:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.ok:
            return response.json()
        response.raise_for_status()

# Function to determine the outcome
def determine_outcome(games):
    for game in games:
        if "Minnesota Timberwolves" in game["HomeTeam"] or "Minnesota Timberwolves" in game["AwayTeam"]:
            if "Oklahoma City Thunder" in game["HomeTeam"] or "Oklahoma City Thunder" in game["AwayTeam"]:
                if game["Status"] == "Final":
                    home_team = game["HomeTeam"]
                    away_team = game["AwayTeam"]
                    home_score = game["HomeTeamScore"]
                    away_score = game["AwayTeamScore"]
                    if home_score > away_score:
                        winner = home_team
                    else:
                        winner = away_team
                    return "recommendation: " + TEAMS[winner]
                elif game["Status"] == "Postponed":
                    return "recommendation: p4"  # Market remains open
                elif game["Status"] == "Canceled":
                    return "recommendation: p3"  # Resolve 50-50
    return "recommendation: p4"  # No game found or in progress

# Main execution
if __name__ == "__main__":
    games = fetch_game_data(DATE)
    result = determine_outcome(games)
    print(result)