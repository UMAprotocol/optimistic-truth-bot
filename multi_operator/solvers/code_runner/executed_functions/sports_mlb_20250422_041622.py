import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Check if API key is available
if not MLB_API_KEY:
    raise ValueError("SPORTS_DATA_IO_MLB_API_KEY not found in environment variables. Please add it to your .env file.")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "Milwaukee Brewers": "p2",
    "San Francisco Giants": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_game_result():
    """
    Fetches the result of the MLB game between Milwaukee Brewers and San Francisco Giants on the specified date.
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
                    home_team = game['HomeTeam']
                    away_team = game['AwayTeam']
                    home_score = game['HomeTeamRuns']
                    away_score = game['AwayTeamRuns']

                    if home_score > away_score:
                        winner = home_team
                    else:
                        winner = away_team

                    return "recommendation: " + RESOLUTION_MAP[winner]
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return "recommendation: p3"
                else:
                    return "recommendation: p4"
        return "recommendation: p4"
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return "recommendation: p4"

def main():
    result = fetch_game_result()
    print(result)

if __name__ == "__main__":
    main()