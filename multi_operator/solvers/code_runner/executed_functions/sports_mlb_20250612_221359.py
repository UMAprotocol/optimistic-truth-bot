import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants for the game
GAME_DATE = "2025-06-12"
HOME_TEAM = "Rockies"
AWAY_TEAM = "Giants"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Rockies": "p1",  # Home team wins
    "Giants": "p2",   # Away team wins
    "50-50": "p3",    # Game canceled or postponed without resolution
    "Too early to resolve": "p4"  # Not enough data or game not yet played
}

def get_game_data(date):
    """Fetch game data for a specific date."""
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def analyze_game_data(games, home_team, away_team):
    """Analyze game data to determine the outcome."""
    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[home_team]
                elif away_score > home_score:
                    return RESOLUTION_MAP[away_team]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["50-50"]
            elif game['Status'] == "Postponed":
                # Check if the game is rescheduled within the season
                rescheduled_game = get_game_data(datetime.strptime(date, "%Y-%m-%d") + datetime.timedelta(days=1))
                if rescheduled_game:
                    return analyze_game_data(rescheduled_game, home_team, away_team)
                else:
                    return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    if games:
        recommendation = analyze_game_data(games, HOME_TEAM, AWAY_TEAM)
    else:
        recommendation = RESOLUTION_MAP["Too early to resolve"]
    print("recommendation:", recommendation)