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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
RESOLUTION_MAP = {
    "NAVI": "p2",  # Natus Vincere
    "NEM": "p1",  # Nemiga
    "50-50": "p3"
}

# Helper functions
def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None

def resolve_match(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{formatted_date}"
    games = get_data(url, HEADERS)
    if not games:
        # Fallback to proxy
        url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{formatted_date}"
        games = get_data(url, HEADERS)
        if not games:
            return "p3"  # Assume 50-50 if data is unavailable

    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                return RESOLUTION_MAP.get(winner, "p3")
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "p3"
            else:
                return "p4"  # Game not completed yet

    return "p4"  # No game found for the given date

# Main execution
if __name__ == "__main__":
    match_date = "2025-06-12"
    team1 = "NAVI"  # Natus Vincere
    team2 = "NEM"  # Nemiga
    recommendation = resolve_match(match_date, team1, team2)
    print(f"recommendation: {recommendation}")