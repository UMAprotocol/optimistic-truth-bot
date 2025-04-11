import os
import requests
from datetime import datetime
from dotenv import load_dotenv

def fetch_game_result():
    load_dotenv()  # Load environment variables from .env file
    api_key = os.getenv('SPORTS_DATA_IO_NHL_API_KEY')
    url = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-10"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if 'Nashville Predators' in game['HomeTeam'] and 'Utah' in game['AwayTeam']:
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return "recommendation: p2"  # Predators win
                    elif away_score > home_score:
                        return "recommendation: p1"  # Utah wins
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"  # Game postponed
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"  # Game canceled, resolve 50-50
        return "recommendation: p4"  # No game found or future game
    except requests.RequestException as e:
        print(f"Failed to fetch data or API error occurred: {e}")
        return "recommendation: p4"  # Unable to fetch data

# Execute the function and print the result
print(fetch_game_result())