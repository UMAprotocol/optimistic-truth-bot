import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# API endpoints
NBA_API_URL = "https://api.sportsdata.io/v3/nba"
NBA_PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

# Constants
GAME_DATE = "2025-06-17"
GAME_TIME = "20:00:00"
TIMEZONE = "ET"
TEAM_A = "Chicago Sky"
TEAM_B = "Washington Mystics"
PLAYER_NAME = "Angel Reese"

def fetch_game_data():
    """
    Fetches game data from the NBA API or its proxy.
    """
    headers = {'Ocp-Apim-Subscription-Key': SPORTS_DATA_IO_NBA_API_KEY}
    date_str = f"{GAME_DATE}T{GAME_TIME}{TIMEZONE}"
    params = {
        'team': TEAM_A,
        'date': date_str
    }

    try:
        # Try fetching from the proxy first
        response = requests.get(f"{NBA_PROXY_URL}/scores/json/GamesByDate/{GAME_DATE}", headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Proxy failed: {e}, falling back to primary API")
        # Fallback to the primary API if proxy fails
        response = requests.get(f"{NBA_API_URL}/scores/json/GamesByDate/{GAME_DATE}", headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

    return data

def analyze_game_data(games):
    """
    Analyzes game data to determine if Angel Reese missed her first shot.
    """
    for game in games:
        if game['HomeTeam'] == TEAM_A or game['AwayTeam'] == TEAM_A:
            if 'PlayerStats' in game:
                for player in game['PlayerStats']:
                    if player['Name'] == PLAYER_NAME:
                        shots = player['FieldGoalsAttempted']
                        made_shots = player['FieldGoalsMade']
                        if shots > 0:
                            if made_shots < shots:
                                return "p2"  # Missed first shot
                            else:
                                return "p1"  # Made first shot
    return "p1"  # Default to "No" if no data found or no shot attempted

def main():
    try:
        games = fetch_game_data()
        result = analyze_game_data(games)
        print(f"recommendation: {result}")
    except Exception as e:
        print(f"Error processing game data: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()