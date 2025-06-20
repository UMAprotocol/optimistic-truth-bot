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
PLAYER_NAME = "Corey Perry"
TEAMS = ["EDM", "FLA"]  # Edmonton Oilers and Florida Panthers

# Resolution map based on the ancillary data
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Function to fetch game data
def fetch_game_data(date):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Function to check if Corey Perry scored a goal
def check_player_goals(games, player_name):
    for game in games:
        if game['Status'] == "Final" and {game['HomeTeam'], game['AwayTeam']} == set(TEAMS):
            players_stats_url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByDate/{GAME_DATE}/{game['GameID']}"
            response = requests.get(players_stats_url, headers=HEADERS)
            if response.status_code == 200:
                player_stats = response.json()
                for stat in player_stats:
                    if stat['Name'] == player_name and stat['Goals'] > 0.5:
                        return "Yes"
                return "No"
    return "Too early to resolve"

# Main function to resolve the market
def resolve_market():
    games = fetch_game_data(GAME_DATE)
    if not games:
        return RESOLUTION_MAP["Too early to resolve"]
    
    result = check_player_goals(games, PLAYER_NAME)
    return RESOLUTION_MAP[result]

# Run the resolution function and print the recommendation
if __name__ == "__main__":
    recommendation = resolve_market()
    print("recommendation:", recommendation)