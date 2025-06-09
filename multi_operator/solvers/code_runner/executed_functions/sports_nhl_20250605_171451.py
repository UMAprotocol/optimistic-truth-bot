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
DATE = "2025-06-05"
TEAM1 = "Complexity"  # p2
TEAM2 = "TYLOO"       # p1
RESOLUTION_MAP = {
    "Complexity": "p2",
    "TYLOO": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Helper functions
def get_json_response(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def find_match_result(date, team1, team2):
    # Construct URL for the specific date
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    games = get_json_response(url, HEADERS)
    if not games:
        return "Too early to resolve"

    # Search for the specific game
    for game in games:
        if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
           (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score == away_score:
                    return "50-50"
                elif (home_score > away_score and game['HomeTeam'] == team1) or \
                     (away_score > home_score and game['AwayTeam'] == team1):
                    return team1
                else:
                    return team2
            elif game['Status'] in ["Canceled", "Postponed"]:
                return "50-50"
            else:
                return "Too early to resolve"
    return "Too early to resolve"

# Main execution
if __name__ == "__main__":
    result = find_match_result(DATE, TEAM1, TEAM2)
    recommendation = RESOLUTION_MAP.get(result, "p4")
    print(f"recommendation: {recommendation}")