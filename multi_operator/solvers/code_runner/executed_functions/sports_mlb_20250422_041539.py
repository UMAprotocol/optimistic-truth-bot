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

def fetch_game_result():
    """
    Fetches the result of the MLB game between Milwaukee Brewers and San Francisco Giants.
    """
    date = "2025-04-21"
    team1 = "Milwaukee Brewers"
    team2 = "San Francisco Giants"
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                if game['Status'] == "Final":
                    home_score = game['HomeTeamRuns']
                    away_score = game['AwayTeamRuns']
                    if home_score > away_score:
                        winner = game['HomeTeam']
                    else:
                        winner = game['AwayTeam']
                    return RESOLUTION_MAP.get(winner, "p4")
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return "p3"
                else:
                    return "p4"
        return "p4"
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
        return "p4"

def main():
    result = fetch_game_result()
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()