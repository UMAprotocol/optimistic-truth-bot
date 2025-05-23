import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
NBA_URL = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/"
NHL_URL = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/"
DATE = "2025-05-22"

# Headers for API requests
NBA_HEADERS = {"Ocp-Apim-Subscription-Key": NBA_API_KEY}
NHL_HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}

# Team abbreviations
TIMBERWOLVES = "MIN"
THUNDER = "OKC"
HURRICANES = "CAR"
PANTHERS = "FLA"

# Resolution map
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "Unknown": "p3"
}

def fetch_game_results(url, headers, team1, team2):
    response = requests.get(url + DATE, headers=headers)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score and game['HomeTeam'] == team1:
                        return "Win"
                    elif away_score > home_score and game['AwayTeam'] == team1:
                        return "Win"
                return "Loss"
    return "Unknown"

def resolve_market():
    nba_result = fetch_game_results(NBA_URL, NBA_HEADERS, TIMBERWOLVES, THUNDER)
    nhl_result = fetch_game_results(NHL_URL, NHL_HEADERS, HURRICANES, PANTHERS)

    if nba_result == "Win" and nhl_result == "Win":
        return RESOLUTION_MAP["Yes"]
    elif nba_result == "Unknown" or nhl_result == "Unknown":
        return RESOLUTION_MAP["Unknown"]
    else:
        return RESOLUTION_MAP["No"]

# Main execution
if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")