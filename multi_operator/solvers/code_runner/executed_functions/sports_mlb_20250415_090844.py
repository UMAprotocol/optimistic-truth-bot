import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants
GAME_DATE = "2025-04-14"
GAME_TIME = "19:45:00"  # 7:45 PM ET in 24-hour format
HOME_TEAM = "St. Louis Cardinals"
AWAY_TEAM = "Houston Astros"
RESOLUTION_MAP = {
    "St. Louis Cardinals": "p1",
    "Houston Astros": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def fetch_game_data(date, home_team, away_team):
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                return game
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return None

def resolve_market(game):
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return "recommendation: " + RESOLUTION_MAP[HOME_TEAM]
        elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
            return "recommendation: " + RESOLUTION_MAP[AWAY_TEAM]
    elif game['Status'] == "Postponed" or game['Status'] == "Delayed":
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    elif game['Status'] == "Canceled":
        return "recommendation: " + RESOLUTION_MAP["50-50"]

    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

def main():
    game = fetch_game_data(GAME_DATE, HOME_TEAM, AWAY_TEAM)
    result = resolve_market(game)
    print(result)

if __name__ == "__main__":
    main()