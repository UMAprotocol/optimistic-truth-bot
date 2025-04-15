import requests
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

def fetch_nhl_game_result():
    # Constants
    TEAM_ABBREVIATIONS = {"Chicago Blackhawks": "CHI", "Montreal Canadiens": "MTL"}
    RESOLUTION_MAP = {
        "CHI": "p2",  # Blackhawks
        "MTL": "p1",  # Canadiens
        "50-50": "p3",
        "Too early to resolve": "p4",
    }
    
    # Game details
    game_date = "2025-04-14"
    team_home = "CHI"
    team_away = "MTL"

    # API request
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}"
    headers = {'Ocp-Apim-Subscription-Key': api_key}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()
        
        # Find the game
        for game in games:
            if game['HomeTeam'] == team_home and game['AwayTeam'] == team_away:
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return "recommendation: " + RESOLUTION_MAP[team_home]
                    elif away_score > home_score:
                        return "recommendation: " + RESOLUTION_MAP[team_away]
                elif game['Status'] == "Postponed":
                    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Canceled":
                    return "recommendation: " + RESOLUTION_MAP["50-50"]
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    except requests.RequestException as e:
        print(f"API request error: {e}")
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Execute the function and print the result
result = fetch_nhl_game_result()
print(result)