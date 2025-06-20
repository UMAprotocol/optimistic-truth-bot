import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Date and teams for the game
GAME_DATE = "2025-06-10"
TEAM1 = "Los Angeles Dodgers"
TEAM2 = "San Diego Padres"

# Resolution map based on game outcome
RESOLUTION_MAP = {
    TEAM1: "p2",  # Dodgers win
    TEAM2: "p1",  # Padres win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "50-50": "p3",  # Game canceled with no make-up
    "Too early to resolve": "p4"  # Not enough data
}

def get_games_by_date(date):
    """Fetch games by date."""
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def resolve_game(games, team1, team2):
    """Resolve the game based on the teams and game status."""
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return RESOLUTION_MAP[game["HomeTeam"]]
                else:
                    return RESOLUTION_MAP[game["AwayTeam"]]
            elif game["Status"] == "Postponed":
                return RESOLUTION_MAP["Postponed"]
            elif game["Status"] == "Canceled":
                return RESOLUTION_MAP["Canceled"]
    return RESOLUTION_MAP["Too early to resolve"]

def main():
    """Main function to resolve the MLB game outcome."""
    game_date = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    games = get_games_by_date(game_date)
    if games:
        recommendation = resolve_game(games, TEAM1, TEAM2)
    else:
        recommendation = RESOLUTION_MAP["Too early to resolve"]
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()