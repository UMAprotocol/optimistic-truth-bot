import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants
RESOLUTION_MAP = {
    "Milwaukee Brewers": "p2",
    "San Francisco Giants": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_result(game_date, home_team, away_team):
    """
    Fetches the result of the specified MLB game.
    """
    primary_url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{game_date}?key={MLB_API_KEY}"
    proxy_url = f"https://minimal-ubuntu-production.up.railway.app/sportsdata-proxy/mlb/GamesByDate/{game_date}?key={MLB_API_KEY}"

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, timeout=10)
        if response.status_code != 200:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(primary_url, timeout=10)
        response.raise_for_status()
        games = response.json()

        # Find the game
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                if game['Status'] == "Final":
                    home_score = game['HomeTeamRuns']
                    away_score = game['AwayTeamRuns']
                    if home_score > away_score:
                        return RESOLUTION_MAP[home_team]
                    elif away_score > home_score:
                        return RESOLUTION_MAP[away_team]
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return RESOLUTION_MAP["50-50"]
                else:
                    return RESOLUTION_MAP["Too early to resolve"]
        return RESOLUTION_MAP["Too early to resolve"]
    except requests.RequestException as e:
        logging.error(f"Network error occurred: {e}")
        return RESOLUTION_MAP["Too early to resolve"]
    except KeyError as e:
        logging.error(f"Error processing game data: {e}")
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    game_date = "2025-04-21"
    home_team = "San Francisco Giants"
    away_team = "Milwaukee Brewers"
    result = fetch_game_result(game_date, home_team, away_team)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()