import requests
from datetime import datetime
from dotenv import load_dotenv
import os

def fetch_game_result():
    load_dotenv()
    api_key = os.getenv('SPORTS_DATA_IO_NBA_API_KEY')
    url = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/2025-04-10"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if game['HomeTeam'] == 'ATL' and game['AwayTeam'] == 'BKN':
                if game['Status'] == 'Final':
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return "p2"  # Hawks win
                    elif away_score > home_score:
                        return "p1"  # Nets win
                elif game['Status'] == 'Postponed':
                    return "p4"  # Game postponed
                elif game['Status'] == 'Canceled':
                    return "p3"  # Game canceled
    return "p4"  # Default to unresolved if no data or other issues

def main():
    recommendation = fetch_game_result()
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()