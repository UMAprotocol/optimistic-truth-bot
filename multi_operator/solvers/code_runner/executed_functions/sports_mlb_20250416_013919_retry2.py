import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def fetch_mlb_game_result():
    api_key = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/2025-04-15?key={api_key}"
    response = requests.get(url)
    games = response.json()

    for game in games:
        if game['HomeTeam'] == "SEA" and game['AwayTeam'] == "CIN":
            game_status = game['Status']
            if game_status == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return "recommendation: p2"  # Seattle Mariners win
                elif away_score > home_score:
                    return "recommendation: p1"  # Cincinnati Reds win
            elif game_status == "Postponed":
                return "recommendation: p4"  # Game postponed, too early to resolve
            elif game_status == "Canceled":
                return "recommendation: p3"  # Game canceled, resolve as 50-50
    return "recommendation: p4"  # No game found or future game, too early to resolve

if __name__ == "__main__":
    recommendation = fetch_mlb_game_result()
    print(recommendation)