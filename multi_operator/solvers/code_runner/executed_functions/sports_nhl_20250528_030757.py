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

def get_games_by_date(date):
    url = f"{PRIMARY_ENDPOINT}{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def analyze_game_results(games):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
            if game["Status"] == "Final":
                home_team_wins = game["HomeTeamScore"] > game["AwayTeamScore"]
                winning_team = game["HomeTeam"] if home_team_wins else game["AwayTeam"]
                return RESOLUTION_MAP[winning_team]
            elif game["Status"] in ["Canceled", "Postponed"]:
                return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

def main():
    games = get_games_by_date(DATE)
    if games is None:
        print("recommendation:", RESOLUTION_MAP["Too early to resolve"])
    else:
        result = analyze_game_results(games)
        print("recommendation:", result)

if __name__ == "__main__":
    main()