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

# Constants for the event
GAME_DATE = "2025-06-12"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}
PLAYER_NAME = "Connor McDavid"

# Resolution conditions
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scores more than 0.5 goals
    "No": "p1",   # Player does not score more than 0.5 goals
    "50-50": "p3" # Game not completed by the specified date
}

# Function to fetch game data
def fetch_game_data(date):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} {response.text}")

# Function to check player goals
def check_player_goals(game_id):
    url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByGame/{game_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        game_stats = response.json()
        for player_stats in game_stats:
            if player_stats["Name"] == PLAYER_NAME:
                return player_stats["Goals"] > 0.5
        return False
    else:
        raise Exception(f"Failed to fetch player stats: {response.status_code} {response.text}")

# Main function to resolve the market
def resolve_market():
    try:
        games = fetch_game_data(GAME_DATE)
        for game in games:
            if {game["HomeTeam"], game["AwayTeam"]} == set(TEAM_ABBREVIATIONS.values()):
                if datetime.now() < datetime.strptime("2025-12-31 23:59", "%Y-%m-%d %H:%M"):
                    if game["Status"] == "Final":
                        if check_player_goals(game["GameID"]):
                            return "recommendation: " + RESOLUTION_MAP["Yes"]
                        else:
                            return "recommendation: " + RESOLUTION_MAP["No"]
                    else:
                        return "recommendation: " + RESOLUTION_MAP["50-50"]
                else:
                    return "recommendation: " + RESOLUTION_MAP["50-50"]
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    except Exception as e:
        print(f"Error: {str(e)}")
        return "recommendation: " + RESOLUTION_MAP["50-50"]

# Run the resolution function
if __name__ == "__main__":
    result = resolve_market()
    print(result)