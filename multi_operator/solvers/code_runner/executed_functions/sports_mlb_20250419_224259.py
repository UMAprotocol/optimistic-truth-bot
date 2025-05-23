import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
import logging

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants
RESOLUTION_MAP = {
    "CLE": "p2",  # Cleveland Guardians win
    "PIT": "p1",  # Pittsburgh Pirates win
    "50-50": "p3",  # Game canceled or postponed without resolution
    "Too early to resolve": "p4"  # Game has not occurred yet or no data available
}
GAME_DATE = "2025-04-19"
GAME_TIME = "16:05:00"
TEAM1 = "Cleveland Guardians"
TEAM2 = "Pittsburgh Pirates"
TIMEZONE = "America/New_York"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_data():
    """
    Fetches game data for the specified date and teams from the SportsDataIO MLB API.
    """
    date = datetime.strptime(f"{GAME_DATE} {GAME_TIME}", "%Y-%m-%d %H:%M:%S")
    date = pytz.timezone(TIMEZONE).localize(date)
    current_time = datetime.now(pytz.timezone(TIMEZONE))

    if current_time < date:
        logging.info("Game has not started yet.")
        return "Too early to resolve"

    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{GAME_DATE}?key={MLB_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == 'CLE' and game['AwayTeam'] == 'PIT' or game['HomeTeam'] == 'PIT' and game['AwayTeam'] == 'CLE':
                if game['Status'] == "Final":
                    home_score = game['HomeTeamRuns']
                    away_score = game['AwayTeamRuns']
                    if home_score > away_score:
                        return RESOLUTION_MAP[game['HomeTeam']]
                    else:
                        return RESOLUTION_MAP[game['AwayTeam']]
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return "50-50"
                else:
                    return "Too early to resolve"
    except requests.RequestException as e:
        logging.error(f"Error fetching game data: {e}")
        return "Too early to resolve"

    return "Too early to resolve"

def main():
    resolution = fetch_game_data()
    print(f"recommendation: {RESOLUTION_MAP.get(resolution, 'p4')}")

if __name__ == "__main__":
    main()