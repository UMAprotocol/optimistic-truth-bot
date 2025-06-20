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
DATE = "2025-06-19"
TEAM1 = "OKC"  # Oklahoma City Thunder
TEAM2 = "IND"  # Indiana Pacers
RESOLUTION_MAP = {
    TEAM1: "p2",  # Thunder win
    TEAM2: "p1",  # Pacers win
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# API Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/"

# Function to fetch game data
def fetch_game_data(date):
    url = f"{PRIMARY_ENDPOINT}{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        return games
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to determine the outcome
def determine_outcome(games, team1, team2):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                home_score = game["HomeTeamScore"]
                away_score = game["AwayTeamScore"]
                if home_score > away_score:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                return RESOLUTION_MAP.get(winner, "Too early to resolve")
            elif game["Status"] in ["Postponed", "Canceled"]:
                return "p3"  # Game postponed or canceled
            else:
                return "p4"  # Game not yet completed
    return "p4"  # No game found or not yet started

# Main execution
if __name__ == "__main__":
    games = fetch_game_data(DATE)
    if games:
        recommendation = determine_outcome(games, TEAM1, TEAM2)
    else:
        recommendation = "p4"  # Unable to fetch data or no games on that date
    print(f"recommendation: {recommendation}")