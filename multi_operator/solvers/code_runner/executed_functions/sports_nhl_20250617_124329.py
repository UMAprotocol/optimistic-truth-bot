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
    "ALC": "p2",  # Alcaraz
    "FOK": "p1",  # Fokina
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Helper functions
def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def resolve_match(date_str, player1, player2):
    # Format the date for API request
    date_formatted = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_formatted}"

    # Try proxy endpoint first
    games = get_data(PROXY_ENDPOINT + url, HEADERS)
    if games is None:
        # Fallback to primary endpoint if proxy fails
        games = get_data(url, HEADERS)

    if games:
        for game in games:
            if {game["HomeTeam"], game["AwayTeam"]} == {player1, player2}:
                if game["Status"] == "Final":
                    winner = game["HomeTeam"] if game["HomeTeamRuns"] > game["AwayTeamRuns"] else game["AwayTeam"]
                    return RESOLUTION_MAP.get(winner, "p4")
                elif game["Status"] in ["Canceled", "Postponed"]:
                    return "p3"
                else:
                    return "p4"
    return "p4"

# Main execution
if __name__ == "__main__":
    # Match details
    match_date = "2025-06-17"
    player1 = "ALC"  # Alcaraz
    player2 = "FOK"  # Fokina

    # Resolve the match and print the recommendation
    recommendation = resolve_match(match_date, player1, player2)
    print(f"recommendation: {recommendation}")