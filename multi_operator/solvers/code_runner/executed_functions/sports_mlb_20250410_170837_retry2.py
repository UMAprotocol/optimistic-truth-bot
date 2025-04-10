import os
from datetime import datetime
import requests

def fetch_nba_game_result():
    # Load environment variables
    api_key = os.getenv('SPORTS_DATA_IO_NBA_API_KEY')
    url = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/2025-04-09"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }

    # Fetch data from API
    response = requests.get(url, headers=headers)
    games = response.json()

    # Define teams and game date
    home_team = "Trail Blazers"
    away_team = "Jazz"
    game_date = "2025-04-09T21:00:00"

    # Process the game data
    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team and game['DateTime'] == game_date:
            if game['Status'] == "Final":
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score:
                    return "recommendation: p2"  # Trail Blazers win
                elif away_score > home_score:
                    return "recommendation: p1"  # Jazz win
            elif game['Status'] == "Postponed":
                return "recommendation: p4"  # Game postponed
            elif game['Status'] == "Canceled":
                return "recommendation: p3"  # Game canceled, resolve 50-50

    return "recommendation: p4"  # Default to too early to resolve if no match found or future game

# Ensure the API key is loaded from .env file
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    print(fetch_nba_game_result())