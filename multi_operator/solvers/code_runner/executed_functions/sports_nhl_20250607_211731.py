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
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
RESOLUTION_MAP = {
    "3DMAX": "p2",  # 3DMAX wins
    "Legacy": "p1",  # Legacy wins
    "50-50": "p3"   # Tie, canceled, or delayed
}
DATE = "2025-06-07"
TEAM1 = "3DMAX"
TEAM2 = "Legacy"

# Function to get game data
def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
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
    if not games:
        return "recommendation: p4"  # Unable to fetch games
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                home_score = game["HomeTeamScore"]
                away_score = game["AwayTeamScore"]
                if home_score > away_score:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                return f"recommendation: {RESOLUTION_MAP[winner]}"
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "recommendation: p3"
            else:
                return "recommendation: p4"  # Game not final
    return "recommendation: p4"  # No matching game found

# Main execution
if __name__ == "__main__":
    games = get_game_data(DATE)
    result = determine_outcome(games, TEAM1, TEAM2)
    print(result)