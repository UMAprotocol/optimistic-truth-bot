import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
GAME_DATE = "2025-06-14"
PLAYER_NAME = "Sam Bennett"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scores more than 0.5 goals
    "No": "p1",   # Player does not score more than 0.5 goals
    "50-50": "p3" # Game not completed by the specified date
}

# Helper function to fetch data from the API
def fetch_game_data(date):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} {response.text}")

# Helper function to check player's goals
def check_player_goals(games, player_name):
    for game in games:
        if game['Status'] == "Final" and {game["HomeTeam"], game["AwayTeam"]} == set(TEAM_ABBREVIATIONS.values()):
            player_stats_url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByDate/{GAME_DATE}/{player_name}"
            response = requests.get(player_stats_url, headers=HEADERS)
            if response.status_code == 200:
                stats = response.json()
                goals = stats.get("Goals", 0)
                return "Yes" if goals > 0.5 else "No"
            else:
                raise Exception(f"Failed to fetch player stats: {response.status_code} {response.text}")
    return "50-50"

# Main function to determine the outcome
def resolve_market():
    try:
        games = fetch_game_data(GAME_DATE)
        result = check_player_goals(games, PLAYER_NAME)
        return f"recommendation: {RESOLUTION_MAP[result]}"
    except Exception as e:
        print(f"Error: {str(e)}")
        return "recommendation: p3"  # Resolve as 50-50 in case of any errors

# Execute the function and print the result
if __name__ == "__main__":
    print(resolve_market())