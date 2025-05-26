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
DATE = "2025-05-24"
TEAM1 = "OKC"  # Oklahoma City Thunder
TEAM2 = "MIN"  # Minnesota Timberwolves
RESOLUTION_MAP = {
    TEAM1: "p2",  # Thunder win
    TEAM2: "p1",  # Timberwolves win
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

def analyze_game_results(games, team1, team2):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                home_team_wins = game["HomeTeam"] == team1 and game["HomeTeamScore"] > game["AwayTeamScore"]
                away_team_wins = game["AwayTeam"] == team1 and game["AwayTeamScore"] > game["HomeTeamScore"]
                if home_team_wins or away_team_wins:
                    return RESOLUTION_MAP[team1] if home_team_wins else RESOLUTION_MAP[team2]
            elif game["Status"] in ["Canceled", "Postponed"]:
                return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

def main():
    games = get_games_by_date(DATE)
    if games is None:
        print("recommendation:", RESOLUTION_MAP["Too early to resolve"])
    else:
        result = analyze_game_results(games, TEAM1, TEAM2)
        print("recommendation:", result)

if __name__ == "__main__":
    main()