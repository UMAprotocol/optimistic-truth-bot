import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Team abbreviations and resolution conditions
RESOLUTION_MAP = {
    "DAL": "p2",  # Dallas Stars
    "EDM": "p1",  # Edmonton Oilers
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if endpoint == PROXY_ENDPOINT:
            print("Proxy failed, trying primary endpoint.")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"HTTP Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    return None

# Function to determine the outcome of the game
def determine_outcome(game_info):
    if not game_info:
        return RESOLUTION_MAP["Too early to resolve"]
    status = game_info.get("Status")
    if status == "Final":
        home_team = game_info["HomeTeam"]
        away_team = game_info["AwayTeam"]
        home_score = game_info["HomeTeamScore"]
        away_score = game_info["AwayTeamScore"]
        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team
        return RESOLUTION_MAP.get(winner, "p3")
    elif status in ["Canceled", "Postponed"]:
        return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main function to execute the program
def main():
    date_today = datetime.now().strftime("%Y-%m-%d")
    game_path = f"/scores/json/GamesByDate/{date_today}"
    games_today = make_request(PROXY_ENDPOINT, game_path)

    if games_today:
        for game in games_today:
            if game["HomeTeam"] == "DAL" and game["AwayTeam"] == "EDM":
                result = determine_outcome(game)
                print(f"recommendation: {result}")
                return
            elif game["HomeTeam"] == "EDM" and game["AwayTeam"] == "DAL":
                result = determine_outcome(game)
                print(f"recommendation: {result}")
                return
    print("recommendation: p4")

if __name__ == "__main__":
    main()