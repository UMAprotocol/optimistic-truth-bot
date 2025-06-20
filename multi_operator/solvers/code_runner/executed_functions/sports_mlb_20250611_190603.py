import os
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Constants
DATE = "2025-06-11"
TEAM1 = "PIT"  # Pittsburgh Pirates
TEAM2 = "MIA"  # Miami Marlins
GAME_TIME = "12:35"
RESOLUTION_MAP = {
    TEAM1: "p1",  # Pittsburgh Pirates win
    TEAM2: "p2",  # Miami Marlins win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Scheduled": "p4"  # Game scheduled but not yet played
}

# API Configuration
API_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_game_data(date):
    url = f"{API_ENDPOINT}{date}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        games = response.json()
        return games
    except requests.RequestException as e:
        logger.error(f"Error fetching game data: {e}")
        return None

def analyze_game(games, team1, team2, game_time):
    for game in games:
        if game['Day'] == DATE and game['Status'] == "Final":
            if game['HomeTeam'] == team1 and game['AwayTeam'] == team2:
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return RESOLUTION_MAP[team1]
                elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                    return RESOLUTION_MAP[team2]
            elif game['HomeTeam'] == team2 and game['AwayTeam'] == team1:
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return RESOLUTION_MAP[team2]
                elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                    return RESOLUTION_MAP[team1]
        elif game['Day'] == DATE and game['Status'] in ["Postponed", "Canceled"]:
            return RESOLUTION_MAP[game['Status']]
    return RESOLUTION_MAP["Scheduled"]

def main():
    games = get_game_data(DATE)
    if games:
        result = analyze_game(games, TEAM1, TEAM2, GAME_TIME)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p4")  # Unable to resolve due to data fetch failure

if __name__ == "__main__":
    main()