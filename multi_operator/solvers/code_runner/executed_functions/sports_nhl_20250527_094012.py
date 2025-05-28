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
THUNDER = "OKC"  # Oklahoma City Thunder abbreviation
PANTHERS = "FLA"  # Florida Panthers abbreviation
TIMBERWOLVES = "MIN"  # Minnesota Timberwolves abbreviation
HURRICANES = "CAR"  # Carolina Hurricanes abbreviation

# API Endpoints
NBA_URL = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/"
NHL_URL = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/"

# Headers for API requests
NBA_HEADERS = {"Ocp-Apim-Subscription-Key": NBA_API_KEY}
NHL_HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}

def get_game_results(sport, date, team1, team2, headers):
    url = f"{sport}{date}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
               (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                if game['Status'] == "Final":
                    return game['Winner'] == team1
                elif game['Status'] in ["Postponed", "Canceled", "Delayed"]:
                    return False
    return None

def resolve_market():
    thunder_win = get_game_results(NBA_URL, DATE, THUNDER, TIMBERWOLVES, NBA_HEADERS)
    panthers_win = get_game_results(NHL_URL, DATE, PANTHERS, HURRICANES, NHL_HEADERS)

    if thunder_win is None or panthers_win is None:
        return "recommendation: p4"  # Unable to resolve now
    elif thunder_win and panthers_win:
        return "recommendation: p2"  # Yes, both win
    else:
        return "recommendation: p1"  # No, one or both did not win

if __name__ == "__main__":
    result = resolve_market()
    print(result)