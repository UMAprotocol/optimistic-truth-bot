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

# Constants
GAME_DATE = "2025-06-17"
PLAYER_NAME = "Sam Reinhart"
TEAMS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scored more than 0.5 goals
    "No": "p1",   # Player did not score more than 0.5 goals
    "50-50": "p3" # Game not completed by the specified date
}

# Function to fetch game data
def fetch_game_data(date, team1, team2):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if team1 in game['HomeTeam'] and team2 in game['AwayTeam']:
                return game
            if team2 in game['HomeTeam'] and team1 in game['AwayTeam']:
                return game
    return None

# Function to check if player scored
def check_player_score(game_id, player_name):
    url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByGame/{game_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        player_stats = response.json()
        for stat in player_stats:
            if player_name in stat['Name']:
                goals = stat.get('Goals', 0)
                return "Yes" if goals > 0.5 else "No"
    return "No"

# Main function to resolve the market
def resolve_market():
    current_date = datetime.now()
    deadline_date = datetime.strptime("2025-12-31 23:59", "%Y-%m-%d %H:%M")
    if current_date > deadline_date:
        return "recommendation: " + RESOLUTION_MAP["50-50"]

    game = fetch_game_data(GAME_DATE, TEAMS["Edmonton Oilers"], TEAMS["Florida Panthers"])
    if not game:
        return "recommendation: " + RESOLUTION_MAP["50-50"]

    result = check_player_score(game['GameID'], PLAYER_NAME)
    return "recommendation: " + RESOLUTION_MAP[result]

# Execute the main function
if __name__ == "__main__":
    print(resolve_market())