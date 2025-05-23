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
HEADERS_NBA = {"Ocp-Apim-Subscription-Key": NBA_API_KEY}
HEADERS_NHL = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}
DATE = "2025-05-22"
TIMBERWOLVES = "MIN"
HURRICANES = "CAR"

def get_game_results(url, headers, team):
    response = requests.get(url + DATE, headers=headers)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if game['HomeTeam'] == team or game['AwayTeam'] == team:
                if game['Status'] == "Final":
                    winning_team = game['HomeTeam'] if game['HomeTeamScore'] > game['AwayTeamScore'] else game['AwayTeam']
                    return winning_team == team
                else:
                    return None
    return None

def resolve_market():
    nba_result = get_game_results(NBA_URL, HEADERS_NBA, TIMBERWOLVES)
    nhl_result = get_game_results(NHL_URL, HEADERS_NHL, HURRICANES)

    if nba_result is None or nhl_result is None:
        return "recommendation: p4"  # Too early to resolve or game not final
    if nba_result and nhl_result:
        return "recommendation: p2"  # Yes, both teams won
    else:
        return "recommendation: p1"  # No, one or both teams did not win

if __name__ == "__main__":
    print(resolve_market())