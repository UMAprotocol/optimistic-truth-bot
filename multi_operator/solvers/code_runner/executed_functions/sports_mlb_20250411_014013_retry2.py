import os
from python_dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Constants
API_KEY = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')
GAME_DATE = "2025-04-10"
HOME_TEAM = "Detroit Red Wings"
AWAY_TEAM = "Florida Panthers"
RESOLUTION_MAP = {
    "Red Wings": "p2",
    "Panthers": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def fetch_game_result():
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{GAME_DATE}?key={API_KEY}"
    response = requests.get(url)
    games = response.json()

    for game in games:
        if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
            if game['Status'] == "Final":
                if game['HomeTeamScore'] > game['AwayTeamScore']:
                    return RESOLUTION_MAP["Red Wings"]
                elif game['AwayTeamScore'] > game['HomeTeamScore']:
                    return RESOLUTION_MAP["Panthers"]
            elif game['Status'] == "Postponed":
                return RESOLUTION_MAP["Too early to resolve"]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

def main():
    recommendation = fetch_game_result()
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()