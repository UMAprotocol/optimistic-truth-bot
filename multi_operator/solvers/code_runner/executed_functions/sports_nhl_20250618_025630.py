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
GAME_DATE = "2025-06-17"
PLAYER_NAME = "Aleksander Barkov"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution map based on the outcome
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scored more than 0.5 goals
    "No": "p1",   # Player did not score more than 0.5 goals
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

# Function to check if player scored
def check_player_score(games, player_name):
    for game in games:
        if game['Status'] == "Final" and (game['HomeTeam'] == TEAM_ABBREVIATIONS["Florida Panthers"] or game['AwayTeam'] == TEAM_ABBREVIATIONS["Florida Panthers"]):
            # Check player stats
            player_stats_url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByDate/{GAME_DATE}/{player_name.replace(' ', '')}"
            player_response = requests.get(player_stats_url, headers=HEADERS)
            if player_response.status_code == 200:
                player_stats = player_response.json()
                goals = player_stats.get('Goals', 0)
                return "Yes" if goals > 0.5 else "No"
            else:
                raise Exception(f"Failed to fetch player stats: {player_response.status_code} {player_response.text}")
    return "No"

# Main function to resolve the market
def resolve_market():
    try:
        games = fetch_game_data(GAME_DATE)
        result = check_player_score(games, PLAYER_NAME)
        return f"recommendation: {RESOLUTION_MAP[result]}"
    except Exception as e:
        print(f"Error: {str(e)}")
        return "recommendation: p4"  # Unable to resolve due to error

# Run the resolution function
if __name__ == "__main__":
    print(resolve_market())