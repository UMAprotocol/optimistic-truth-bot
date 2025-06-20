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
GAME_DATE = "2025-06-14"
PLAYER_NAME = "Brad Marchand"
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
        raise Exception(f"Failed to fetch data: {response.status_code} {response.text}")

# Function to check if player scored
def check_player_score(games, player_name):
    for game in games:
        if game['HomeTeam'] in TEAMS and game['AwayTeam'] in TEAMS:
            if game['Status'] == "Final":
                player_stats_url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByDate/{GAME_DATE}/{player_name.replace(' ', '')}"
                response = requests.get(player_stats_url, headers=HEADERS)
                if response.status_code == 200:
                    stats = response.json()
                    goals = stats[0]['Goals'] if stats else 0
                    return "Yes" if goals > 0.5 else "No"
                else:
                    raise Exception(f"Failed to fetch player stats: {response.status_code} {response.text}")
            else:
                return "50-50"
    return "50-50"

# Main function to resolve the market
def resolve_market():
    try:
        games = fetch_game_data(GAME_DATE)
        result = check_player_score(games, PLAYER_NAME)
        return f"recommendation: {RESOLUTION_MAP[result]}"
    except Exception as e:
        print(f"Error: {str(e)}")
        return "recommendation: p3"  # Resolve as unknown/50-50 in case of errors

# Run the resolver
if __name__ == "__main__":
    print(resolve_market())