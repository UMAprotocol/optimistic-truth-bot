import requests
from dotenv import load_dotenv
import os

def fetch_nba_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
    url = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/2025-04-15"
    headers = {
        "Ocp-Apim-Subscription-Key": api_key
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] == "ATL" and game['AwayTeam'] == "ORL":
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return "recommendation: p2"  # Hawks win
                    elif away_score > home_score:
                        return "recommendation: p1"  # Magic win
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"  # Game postponed
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"  # Game canceled, resolve 50-50
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: p4"  # Unable to resolve due to error

    return "recommendation: p4"  # Default case if no specific condition is met

# Example usage
result = fetch_nba_game_result()
print(result)