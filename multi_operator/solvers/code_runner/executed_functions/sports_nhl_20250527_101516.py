import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
DATE = "2025-05-26"
TIMBERWOLVES = "MIN"  # Minnesota Timberwolves
HURRICANES = "CAR"    # Carolina Hurricanes
THUNDER = "OKC"       # Oklahoma City Thunder
PANTHERS = "FLA"      # Florida Panthers

# Headers for API requests
NBA_HEADERS = {"Ocp-Apim-Subscription-Key": NBA_API_KEY}
NHL_HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}

# API endpoints
NBA_URL = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/"
NHL_URL = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/"

def get_game_results(sport, date, team1, team2, headers):
    url = f"{sport}{date}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if {game['HomeTeam'], game['AwayTeam']} == {team1, team2}:
                if game['Status'] == "Final":
                    winner = game['HomeTeam'] if game['HomeTeamRuns'] > game['AwayTeamRuns'] else game['AwayTeam']
                    return winner == team1
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return False
    return None

def resolve_market():
    nba_result = get_game_results(NBA_URL, DATE, TIMBERWOLVES, THUNDER, NBA_HEADERS)
    nhl_result = get_game_results(NHL_URL, DATE, HURRICANES, PANTHERS, NHL_HEADERS)

    if nba_result is None or nhl_result is None:
        return "recommendation: p4"  # Unable to resolve now
    if nba_result and nhl_result:
        return "recommendation: p2"  # Yes, both teams won
    return "recommendation: p1"      # No, one or both teams did not win

# Run the market resolution
if __name__ == "__main__":
    print(resolve_market())