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

def get_games_by_date(url, headers):
    response = requests.get(url + DATE, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def check_team_win(games, team_name):
    for game in games:
        if (game['HomeTeam'] == team_name or game['AwayTeam'] == team_name) and game['Status'] == "Final":
            if game['HomeTeam'] == team_name and game['HomeTeamScore'] > game['AwayTeamScore']:
                return True
            elif game['AwayTeam'] == team_name and game['AwayTeamScore'] > game['HomeTeamScore']:
                return True
    return False

def main():
    nba_games = get_games_by_date(NBA_URL, NBA_HEADERS)
    nhl_games = get_games_by_date(NHL_URL, NHL_HEADERS)

    if nba_games is None or nhl_games is None:
        print("recommendation: p3")  # Unknown due to API failure
        return

    timberwolves_win = check_team_win(nba_games, "MIN")
    hurricanes_win = check_team_win(nhl_games, "CAR")

    if timberwolves_win and hurricanes_win:
        print("recommendation: p2")  # Yes, both teams won
    else:
        print("recommendation: p1")  # No, one or both teams did not win

if __name__ == "__main__":
    main()