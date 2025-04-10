import os
import requests
from datetime import datetime
from dotenv import load_dotenv

def fetch_nba_game_result():
    load_dotenv()
    api_key = os.getenv('SPORTS_DATA_IO_NBA_API_KEY')
    date_of_game = '2025-04-09'
    team_a = 'Portland Trail Blazers'
    team_b = 'Utah Jazz'

    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date_of_game}?key={api_key}"
    response = requests.get(url)
    games = response.json()

    for game in games:
        if (team_a in game['HomeTeam'] or team_a in game['AwayTeam']) and (team_b in game['HomeTeam'] or team_b in game['AwayTeam']):
            if game['Status'] == 'Scheduled':
                return 'p4'  # Game has not yet been played
            elif game['Status'] == 'Canceled':
                return 'p3'  # Game canceled with no make-up date
            elif game['Status'] == 'Final':
                if game['HomeTeam'] == team_a and game['HomeTeamScore'] > game['AwayTeamScore']:
                    return 'p2'  # Trail Blazers win
                elif game['AwayTeam'] == team_a and game['AwayTeamScore'] > game['HomeTeamScore']:
                    return 'p2'  # Trail Blazers win
                else:
                    return 'p1'  # Jazz win
    return 'p4'  # No relevant game found or game is in the future

recommendation = fetch_nba_game_result()
print(f"recommendation: {recommendation}")