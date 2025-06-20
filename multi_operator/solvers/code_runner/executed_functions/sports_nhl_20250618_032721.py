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
GAME_DATE = "2025-06-17"
TEAM1 = "EDM"  # Edmonton Oilers
TEAM2 = "FLA"  # Florida Panthers
RESOLUTION_MAP = {
    TEAM1: "p2",  # Oilers win
    TEAM2: "p1",  # Panthers win
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Function to make API requests
def make_request(url, tag, use_proxy=False):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during {tag}: {str(e)}")
        if use_proxy:
            proxy_url = url.replace("https://api.sportsdata.io", "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy")
            return make_request(proxy_url, tag, use_proxy=False)
        return None

# Function to find and resolve the game outcome
def resolve_game():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date_formatted}"
    games = make_request(url, "GamesByDate", use_proxy=True)
    
    if not games:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
            if game["Status"] == "Final":
                if game["HomeTeam"] == TEAM1 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return "recommendation: " + RESOLUTION_MAP[TEAM1]
                elif game["AwayTeam"] == TEAM1 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return "recommendation: " + RESOLUTION_MAP[TEAM1]
                elif game["HomeTeam"] == TEAM2 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return "recommendation: " + RESOLUTION_MAP[TEAM2]
                elif game["AwayTeam"] == TEAM2 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return "recommendation: " + RESOLUTION_MAP[TEAM2]
            elif game["Status"] == "Postponed":
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
            elif game["Status"] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    result = resolve_game()
    print(result)