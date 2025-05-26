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

# Function to fetch game results
def fetch_game_results(url, headers):
    response = requests.get(url + DATE, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Function to check if team won
def check_if_team_won(games, team):
    for game in games:
        if (game['HomeTeam'] == team or game['AwayTeam'] == team) and game['Status'] == "Final":
            if game['HomeTeam'] == team and game['HomeTeamScore'] > game['AwayTeamScore']:
                return True
            elif game['AwayTeam'] == team and game['AwayTeamScore'] > game['HomeTeamScore']:
                return True
    return False

# Main function to determine the outcome
def determine_outcome():
    nba_games = fetch_game_results(NBA_URL, HEADERS_NBA)
    nhl_games = fetch_game_results(NHL_URL, HEADERS_NHL)
    
    if nba_games is None or nhl_games is None:
        return "recommendation: p4"  # Unable to fetch data

    thunder_won = check_if_team_won(nba_games, "OKC")
    panthers_won = check_if_team_won(nhl_games, "FLA")

    if thunder_won and panthers_won:
        return "recommendation: p2"  # Both teams won
    else:
        return "recommendation: p1"  # At least one team did not win

# Execute the main function
if __name__ == "__main__":
    result = determine_outcome()
    print(result)