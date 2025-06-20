import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}
GAME_DATE = "2025-06-14"
PLAYER_NAME = "Leon Draisaitl"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution map
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scores more than 0.5 goals
    "No": "p1",   # Player does not score more than 0.5 goals
    "50-50": "p3" # Game not completed by the specified date
}

def get_game_data():
    try:
        # Try proxy endpoint first
        response = requests.get(f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}", headers=HEADERS, timeout=10)
        if not response.ok:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching game data: {e}")
        return None

def analyze_game_data(games):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == set(TEAM_ABBREVIATIONS.values()):
            if game["Status"] == "Final":
                for player in game["PlayerStats"]:
                    if player["Name"] == PLAYER_NAME and player["Goals"] > 0.5:
                        return "Yes"
                return "No"
            elif game["Day"].date() > datetime.strptime("2025-12-31", "%Y-%m-%d").date():
                return "50-50"
    return "50-50"

def main():
    games = get_game_data()
    if games:
        result = analyze_game_data(games)
        recommendation = RESOLUTION_MAP[result]
        print(f"recommendation: {recommendation}")
    else:
        print("recommendation: p3")  # Assume 50-50 if no data could be fetched

if __name__ == "__main__":
    main()