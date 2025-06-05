import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants
DATE = "2025-06-04"
TEAM1 = "Seattle Mariners"
TEAM2 = "Baltimore Orioles"
RESOLUTION_MAP = {
    "Mariners": "p1",
    "Orioles": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Function to make API requests
def make_request(url, proxy_url=None):
    try:
        response = requests.get(proxy_url if proxy_url else url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if proxy_url:
            # Fallback to primary endpoint if proxy fails
            return make_request(url)
        else:
            print(f"Error: {str(e)}")
            return None

# Function to find and resolve the game outcome
def resolve_game(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{formatted_date}"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

    games = make_request(url, proxy_url)
    if games is None:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                home_team_wins = game["HomeTeamRuns"] > game["AwayTeamRuns"]
                away_team_wins = game["AwayTeamRuns"] > game["HomeTeamRuns"]
                if home_team_wins:
                    return "recommendation: " + RESOLUTION_MAP[game["HomeTeam"]]
                elif away_team_wins:
                    return "recommendation: " + RESOLUTION_MAP[game["AwayTeam"]]
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            else:
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    result = resolve_game(DATE, TEAM1, TEAM2)
    print(result)