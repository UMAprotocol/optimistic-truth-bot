import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

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

# Function to make API requests
def make_request(url, proxy_url=None):
    try:
        response = requests.get(proxy_url if proxy_url else url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            if proxy_url:
                # Retry with primary URL if proxy fails
                return make_request(url)
            response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to find the game and determine the outcome
def resolve_nhl_game(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{formatted_date}"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

    games = make_request(url, proxy_url)
    if games is None:
        return RESOLUTION_MAP["Too early to resolve"]

    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeam"] == team1 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return RESOLUTION_MAP[team1]
                elif game["AwayTeam"] == team1 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return RESOLUTION_MAP[team1]
                elif game["HomeTeam"] == team2 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return RESOLUTION_MAP[team2]
                elif game["AwayTeam"] == team2 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return RESOLUTION_MAP[team2]
            elif game["Status"] == "Postponed":
                return RESOLUTION_MAP["Too early to resolve"]
            elif game["Status"] == "Canceled":
                return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    recommendation = resolve_nhl_game(DATE, TEAM1, TEAM2)
    print(f"recommendation: {recommendation}")