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
DATE = "2025-05-27"
TEAM1 = "NYK"  # New York Knicks
TEAM2 = "IND"  # Indiana Pacers
RESOLUTION_MAP = {
    TEAM1: "p2",  # Knicks win
    TEAM2: "p1",  # Pacers win
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# API Configuration
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        return games
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def analyze_game(games, team1, team2):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                home_score = game["HomeTeamScore"]
                away_score = game["AwayTeamScore"]
                if home_score > away_score:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                return RESOLUTION_MAP.get(winner, "p4")
            elif game["Status"] in ["Postponed", "Canceled"]:
                return "p3"
            else:
                return "p4"
    return "p4"

def main():
    games = get_game_data(DATE)
    if games is None:
        print("recommendation: p4")
        return
    result = analyze_game(games, TEAM1, TEAM2)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()