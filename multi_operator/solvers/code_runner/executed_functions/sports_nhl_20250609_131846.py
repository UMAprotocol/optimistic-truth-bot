import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# NHL team abbreviations
RESOLUTION_MAP = {
    "EDM": "p2",  # Edmonton Oilers
    "DAL": "p1",  # Dallas Stars
    "50-50": "p3",
    "Too early to resolve": "p4",
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
def resolve_game(date_str, team1, team2):
    formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{formatted_date}"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

    games = make_request(url, proxy_url)
    if games is None:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeam"] == team1 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return "recommendation: " + RESOLUTION_MAP[team1]
                elif game["AwayTeam"] == team1 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return "recommendation: " + RESOLUTION_MAP[team1]
                else:
                    return "recommendation: " + RESOLUTION_MAP[team2]
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            else:
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    game_date = "2025-05-29"
    team1_abbr = "EDM"  # Edmonton Oilers
    team2_abbr = "DAL"  # Dallas Stars
    result = resolve_game(game_date, team1_abbr, team2_abbr)
    print(result)