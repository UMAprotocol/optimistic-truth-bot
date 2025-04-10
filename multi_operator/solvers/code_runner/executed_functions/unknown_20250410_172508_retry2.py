import os
import requests
from datetime import datetime
from dotenv import load_dotenv

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv('SPORTS_DATA_IO_NHL_API_KEY')
    url = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-09"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }
    
    try:
        response = requests.get(url, headers=headers)
        games = response.json()
        
        for game in games:
            if 'Toronto Maple Leafs' in game['HomeTeam'] and 'Tampa Bay Lightning' in game['AwayTeam']:
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return "recommendation: p2"  # Maple Leafs win
                    elif away_score > home_score:
                        return "recommendation: p1"  # Lightning win
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"  # Game postponed
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"  # Game canceled, resolve 50-50
        return "recommendation: p4"  # No specific game found or future game
    except Exception as e:
        print(f"Error: {str(e)}")
        return "recommendation: p4"  # In case of any error, too early to resolve

# Run the function and print the result
print(fetch_nhl_game_result())