import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Date and teams for the game
GAME_DATE = "2025-06-15"
HOME_TEAM = "Cubs"
AWAY_TEAM = "Pirates"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Cubs": "p1",       # Home team wins
    "Pirates": "p2",    # Away team wins
    "50-50": "p3",      # Game canceled or tie
    "Too early to resolve": "p4"  # Not enough data or game not completed
}

def get_game_data(date):
    """Fetch game data for a specific date."""
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS, timeout=10)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def analyze_game_data(games, home_team, away_team):
    """Analyze game data to determine the outcome."""
    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == 'Final':
                home_runs = game['HomeTeamRuns']
                away_runs = game['AwayTeamRuns']
                if home_runs > away_runs:
                    return RESOLUTION_MAP[home_team]
                elif away_runs > home_runs:
                    return RESOLUTION_MAP[away_team]
            elif game['Status'] == 'Canceled':
                return RESOLUTION_MAP["50-50"]
            elif game['Status'] == 'Postponed':
                # Check if the game is rescheduled within the next day
                next_day = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
                next_day_games = get_game_data(next_day)
                if next_day_games:
                    return analyze_game_data(next_day_games, home_team, away_team)
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    if games:
        recommendation = analyze_game_data(games, HOME_TEAM, AWAY_TEAM)
    else:
        recommendation = RESOLUTION_MAP["Too early to resolve"]
    print("recommendation:", recommendation)