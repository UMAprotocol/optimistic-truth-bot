import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}

# Constants
GAME_DATE = "2025-06-14"
PLAYER_NAME = "Sam Reinhart"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution map based on the outcome
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "50-50": "p3"
}

def get_game_data(date, team1, team2):
    """Fetch game data for a specific date and teams."""
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if {game['HomeTeam'], game['AwayTeam']} == {team1, team2}:
                return game
    return None

def check_player_goals(game_id, player_name):
    """Check if the specified player scored a goal in the game."""
    url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByGame/{game_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == player_name and stat['Goals'] > 0:
                return True
    return False

def resolve_market():
    """Resolve the market based on the player's performance."""
    game = get_game_data(GAME_DATE, TEAM_ABBREVIATIONS["Edmonton Oilers"], TEAM_ABBREVIATIONS["Florida Panthers"])
    if game:
        if datetime.now() > datetime.strptime("2025-12-31 23:59", "%Y-%m-%d %H:%M"):
            return RESOLUTION_MAP["50-50"]
        if game['Status'] == 'Final':
            if check_player_goals(game['GameID'], PLAYER_NAME):
                return RESOLUTION_MAP["Yes"]
            else:
                return RESOLUTION_MAP["No"]
        else:
            return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["50-50"]

if __name__ == "__main__":
    result = resolve_market()
    print("recommendation:", result)