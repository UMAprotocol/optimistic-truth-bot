import requests
from dotenv import load_dotenv
import os
import datetime

# Load environment variables
load_dotenv()

# Constants
SPORTS_DATA_IO_API_KEY = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')
SPORTS_DATA_IO_NBA_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}"

# Game details
game_date = "2025-04-09"
teams = {"Miami Heat": "Heat", "Chicago Bulls": "Bulls"}

def fetch_game_data(date):
    """
    Fetch NBA game data for a specific date.
    """
    url = SPORTS_DATA_IO_NBA_ENDPOINT.format(date=date)
    headers = {'Ocp-Apim-Subscription-Key': SPORTS_DATA_IO_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} - {response.text}")

def resolve_market(games):
    """
    Resolve the market based on the game outcome.
    """
    for game in games:
        if game['HomeTeam'] in teams and game['AwayTeam'] in teams:
            if game['Status'] == "Final":
                if game['HomeTeamScore'] > game['AwayTeamScore']:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                return f"recommendation: p2" if teams[winner] == "Heat" else f"recommendation: p1"
            elif game['Status'] == "Postponed":
                return "recommendation: p3"
            elif game['Status'] == "Canceled":
                return "recommendation: p3"
    return "recommendation: p3"  # Default to unknown if no matching game is found

def main():
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if today > game_date:
            games = fetch_game_data(game_date)
            result = resolve_market(games)
            print(result)
        else:
            print("recommendation: p4")  # Game has not occurred yet
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()