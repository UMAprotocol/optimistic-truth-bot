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
game_date = "2025-04-10"
teams = ("Cavaliers", "Pacers")

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
    Resolve the market based on game results.
    """
    for game in games:
        if teams[0] in game['HomeTeam'] and teams[1] in game['AwayTeam'] or teams[1] in game['HomeTeam'] and teams[0] in game['AwayTeam']:
            if game['Status'] == "Final":
                if game['HomeTeam'] == teams[0] and game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "recommendation: p2"  # Cavaliers win
                elif game['HomeTeam'] == teams[1] and game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "recommendation: p1"  # Pacers win
                elif game['AwayTeam'] == teams[0] and game['AwayTeamScore'] > game['HomeTeamScore']:
                    return "recommendation: p2"  # Cavaliers win
                elif game['AwayTeam'] == teams[1] and game['AwayTeamScore'] > game['HomeTeamScore']:
                    return "recommendation: p1"  # Pacers win
            elif game['Status'] == "Postponed":
                return "recommendation: p3"  # Market remains open
            elif game['Status'] == "Canceled":
                return "recommendation: p3"  # Resolve 50-50
    return "recommendation: p3"  # If no specific game found or other conditions

def main():
    try:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if today > game_date:
            games = fetch_game_data(game_date)
            result = resolve_market(games)
            print(result)
        else:
            print("Game has not occurred yet.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()