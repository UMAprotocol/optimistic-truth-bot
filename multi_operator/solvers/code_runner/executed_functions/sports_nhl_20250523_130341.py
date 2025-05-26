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
THUNDER = "OKC"
PANTHERS = "FLA"

def fetch_games(api_url, headers):
    response = requests.get(api_url + DATE, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def check_team_win(games, team_code):
    if games:
        for game in games:
            if team_code in [game['HomeTeam'], game['AwayTeam']]:
                if game['Status'] == "Final":
                    winning_team = game['HomeTeam'] if game['HomeTeamScore'] > game['AwayTeamScore'] else game['AwayTeam']
                    return winning_team == team_code
                else:
                    return False
    return False

def main():
    nba_games = fetch_games(NBA_URL, HEADERS_NBA)
    nhl_games = fetch_games(NHL_URL, HEADERS_NHL)

    thunder_win = check_team_win(nba_games, THUNDER)
    panthers_win = check_team_win(nhl_games, PANTHERS)

    if thunder_win and panthers_win:
        print("recommendation: p2")  # Both teams won
    else:
        print("recommendation: p1")  # At least one team did not win

if __name__ == "__main__":
    main()