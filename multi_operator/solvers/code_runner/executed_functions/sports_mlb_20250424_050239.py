import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "Tampa Bay Rays": "p2",
    "Arizona Diamondbacks": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_result(game_date, home_team, away_team):
    """
    Fetches the result of a specific MLB game.
    """
    primary_url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{game_date}?key={MLB_API_KEY}"
    proxy_url = f"https://minimal-ubuntu-production.up.railway.app/mlb-proxy/GamesByDate/{game_date}?key={MLB_API_KEY}"

    try:
        # Try fetching via proxy first
        response = requests.get(proxy_url, timeout=10)
        if response.status_code != 200:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(primary_url, timeout=10)
            response.raise_for_status()
        
        games = response.json()
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
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch game data: {e}")
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to determine the outcome of the MLB game between Tampa Bay Rays and Arizona Diamondbacks.
    """
    game_date = "2025-04-23"
    home_team = "Arizona Diamondbacks"
    away_team = "Tampa Bay Rays"
    result = fetch_game_result(game_date, home_team, away_team)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()