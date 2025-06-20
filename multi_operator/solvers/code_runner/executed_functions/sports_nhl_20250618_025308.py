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
GAME_DATE = "2025-06-17"
PLAYER_NAME = "Leon Draisaitl"
TEAMS = ["EDM", "FLA"]  # Edmonton Oilers and Florida Panthers
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "50-50": "p3"
}

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}

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
        if game['HomeTeam'] in TEAMS and game['AwayTeam'] in TEAMS:
            if game['Status'] == "Final":
                for player in game['PlayerGames']:
                    if player['Name'] == player_name and player['Goals'] > 0:
                        return "Yes"
                return "No"
            else:
                return "50-50"
    return "50-50"

# Main function to resolve the market
def resolve_market():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if today > GAME_DATE:
        games = fetch_game_data(GAME_DATE)
        if games:
            result = check_player_score(games, PLAYER_NAME)
            return f"recommendation: {RESOLUTION_MAP[result]}"
        else:
            return "recommendation: p3"  # Assume 50-50 if no data
    else:
        return "recommendation: p3"  # 50-50 if the game date has not passed

# Run the main function
if __name__ == "__main__":
    print(resolve_market())