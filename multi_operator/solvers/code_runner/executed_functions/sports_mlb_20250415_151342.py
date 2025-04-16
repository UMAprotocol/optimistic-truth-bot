import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants
GAME_DATE = "2025-04-14"
GAME_TIME = "22:10"
HOME_TEAM = "Los Angeles Dodgers"
AWAY_TEAM = "Colorado Rockies"
RESOLUTION_MAP = {
    "Los Angeles Dodgers": "p1",
    "Colorado Rockies": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def fetch_game_result():
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{GAME_DATE}?key={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['DateTime'].startswith(GAME_DATE + "T" + GAME_TIME) and \
               game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
                if game['Status'] == "Final":
                    if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                        return RESOLUTION_MAP[HOME_TEAM]
                    elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
                        return RESOLUTION_MAP[AWAY_TEAM]
                elif game['Status'] == "Postponed":
                    return RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Canceled":
                    return RESOLUTION_MAP["50-50"]
        return RESOLUTION_MAP["Too early to resolve"]
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    result = fetch_game_result()
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()