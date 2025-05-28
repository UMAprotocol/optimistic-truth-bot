import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
RESOLUTION_MAP = {
    "DAL": "p2",  # Dallas Stars
    "EDM": "p1",  # Edmonton Oilers
    "50-50": "p3",
    "Too early to resolve": "p4",
}
GAME_DATE = "2025-05-27"
GAME_TIME = "20:00:00"

# Helper functions
def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def analyze_game(games):
    for game in games:
        if game['AwayTeam'] == "DAL" and game['HomeTeam'] == "EDM":
            if game['Status'] == "Final":
                away_score = game['AwayTeamRuns']
                home_score = game['HomeTeamRuns']
                if away_score > home_score:
                    return RESOLUTION_MAP["DAL"]
                elif home_score > away_score:
                    return RESOLUTION_MAP["EDM"]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["50-50"]
            elif game['Status'] == "Scheduled":
                game_time = datetime.strptime(game['DateTime'], "%Y-%m-%dT%H:%M:%S")
                if game_time.time().strftime("%H:%M:%S") == GAME_TIME:
                    return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    if games:
        recommendation = analyze_game(games)
    else:
        recommendation = RESOLUTION_MAP["Too early to resolve"]
    print(f"recommendation: {recommendation}")