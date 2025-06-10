import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Game details
GAME_DATE = "2025-05-29"
TEAM1 = "Punjab Kings"
TEAM2 = "Royal Challengers Bangalore"

# Resolution map
RESOLUTION_MAP = {
    TEAM1: "p2",  # Punjab Kings win
    TEAM2: "p1",  # Royal Challengers Bangalore win
    "Canceled": "p3",  # Game canceled
    "Postponed": "p4",  # Game postponed
    "Unknown": "p4"  # Unknown or in-progress
}

def get_game_data(date):
    """Fetch game data for a specific date."""
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def analyze_game_data(games, team1, team2):
    """Analyze game data to determine the outcome."""
    for game in games:
        if team1 in game['Teams'] and team2 in game['Teams']:
            if game['Status'] == "Final":
                if game['Winner'] == team1:
                    return RESOLUTION_MAP[team1]
                elif game['Winner'] == team2:
                    return RESOLUTION_MAP[team2]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["Canceled"]
            elif game['Status'] == "Postponed":
                return RESOLUTION_MAP["Postponed"]
    return RESOLUTION_MAP["Unknown"]

def main():
    """Main function to resolve the game outcome."""
    games = get_game_data(GAME_DATE)
    if games:
        result = analyze_game_data(games, TEAM1, TEAM2)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p4")  # No data available

if __name__ == "__main__":
    main()