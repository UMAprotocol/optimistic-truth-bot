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

# Analyze game results
def analyze_results(nba_games, nhl_games, nba_team, nhl_team):
    nba_win = any(game for game in nba_games if game['Status'] == 'Final' and 
                  ((game['HomeTeam'] == nba_team or game['AwayTeam'] == nba_team) and 
                   ((game['HomeTeam'] == nba_team and game['HomeTeamScore'] > game['AwayTeamScore']) or 
                    (game['AwayTeam'] == nba_team and game['AwayTeamScore'] > game['HomeTeamScore']))))
    
    nhl_win = any(game for game in nhl_games if game['Status'] == 'Final' and 
                  ((game['HomeTeam'] == nhl_team or game['AwayTeam'] == nhl_team) and 
                   ((game['HomeTeam'] == nhl_team and game['HomeTeamScore'] > game['AwayTeamScore']) or 
                    (game['AwayTeam'] == nhl_team and game['AwayTeamScore'] > game['HomeTeamScore']))))
    
    if nba_win and nhl_win:
        return "p2"  # Both teams won
    else:
        return "p1"  # At least one team did not win

# Main execution
if __name__ == "__main__":
    nba_results = fetch_game_results(NBA_URL, HEADERS_NBA)
    nhl_results = fetch_game_results(NHL_URL, HEADERS_NHL)
    
    if nba_results is None or nhl_results is None:
        print("recommendation: p3")  # Unable to fetch results
    else:
        recommendation = analyze_results(nba_results, nhl_results, "OKC", "FLA")
        print(f"recommendation: {recommendation}")