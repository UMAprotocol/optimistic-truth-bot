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

# Constants for the game and player in question
GAME_DATE = "2025-06-14"
PLAYER_NAME = "Sam Bennett"
TEAMS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

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
        return None

# Function to check if player scored
def check_player_score(games, player_name):
    for game in games:
        if game['Status'] == 'Final' and (game['HomeTeam'] in TEAMS.values() or game['AwayTeam'] in TEAMS.values()):
            game_id = game['GameID']
            url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByGame/{game_id}"
            response = requests.get(url, headers=HEADERS)
            if response.status_code == 200:
                player_stats = response.json()
                for stat in player_stats:
                    if stat['Name'] == player_name and stat['Goals'] > 0.5:
                        return "Yes"
    return "No"

# Main function to resolve the market
def resolve_market():
    current_date = datetime.now()
    deadline_date = datetime.strptime("2025-12-31 23:59", "%Y-%m-%d %H:%M")
    if current_date > deadline_date:
        return RESOLUTION_MAP["50-50"]

    games = fetch_game_data(GAME_DATE)
    if not games:
        return RESOLUTION_MAP["50-50"]

    result = check_player_score(games, PLAYER_NAME)
    return RESOLUTION_MAP[result]

# Run the resolution function and print the recommendation
if __name__ == "__main__":
    recommendation = resolve_market()
    print("recommendation:", recommendation)