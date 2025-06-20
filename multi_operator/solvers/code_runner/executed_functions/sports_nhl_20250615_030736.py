import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
DATE = "2025-06-14"
TEAM1 = "FLA"  # Florida Panthers
TEAM2 = "EDM"  # Edmonton Oilers
RESOLUTION_MAP = {
    TEAM1: "p2",  # Panthers win
    TEAM2: "p1",  # Oilers win
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# API Configuration
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/"
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
    if not games:
        return "Too early to resolve"
    for game in games:
        if game['Day'] == DATE and {game['HomeTeam'], game['AwayTeam']} == {TEAM1, TEAM2}:
            if game['Status'] == "Final":
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                return RESOLUTION_MAP.get(winner, "Too early to resolve")
            elif game['Status'] in ["Canceled", "Postponed"]:
                return "50-50"
    return "Too early to resolve"

def main():
    games = get_games_by_date(DATE)
    result = analyze_game_results(games)
    print("recommendation:", RESOLUTION_MAP.get(result, "Too early to resolve"))

if __name__ == "__main__":
    main()