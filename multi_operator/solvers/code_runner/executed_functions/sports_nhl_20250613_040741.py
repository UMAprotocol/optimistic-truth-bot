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

# NHL Game and Player Information
GAME_DATE = "2025-06-12"
PLAYER_NAME = "Carter Verhaeghe"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

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

# Function to check player's goal in a game
def check_player_goals(game_id, player_name):
    url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByGame/{game_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        players_stats = response.json()
        for player_stat in players_stats:
            if player_stat["Name"] == player_name:
                goals = player_stat.get("Goals", 0)
                return "Yes" if goals > 0.5 else "No"
        return "No"
    else:
        raise Exception(f"Failed to fetch player stats: {response.status_code} {response.text}")

# Main function to resolve the market
def resolve_market():
    try:
        games = fetch_game_data(GAME_DATE)
        for game in games:
            if game["HomeTeam"] in TEAM_ABBREVIATIONS.values() and game["AwayTeam"] in TEAM_ABBREVIATIONS.values():
                game_id = game["GameID"]
                result = check_player_goals(game_id, PLAYER_NAME)
                return f"recommendation: {RESOLUTION_MAP[result]}"
        return f"recommendation: {RESOLUTION_MAP['50-50']}"
    except Exception as e:
        print(f"Error: {str(e)}")
        return f"recommendation: {RESOLUTION_MAP['50-50']}"

# Run the main function
if __name__ == "__main__":
    print(resolve_market())