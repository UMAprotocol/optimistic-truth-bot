import requests
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables
load_dotenv()
api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
TEAM_ABBREVIATIONS = {
    "Chicago Blackhawks": "CHI",
    "Montreal Canadiens": "MTL"
}
RESOLUTION_MAP = {
    "CHI": "p2",  # Blackhawks
    "MTL": "p1",  # Canadiens
    "50-50": "p3",
    "Too early to resolve": "p4",
}

def fetch_game_result():
    url = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-14"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] in TEAM_ABBREVIATIONS.values() and game['AwayTeam'] in TEAM_ABBREVIATIONS.values():
                if game['Status'] == "Final":
                    home_team = game['HomeTeam']
                    away_team = game['AwayTeam']
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return RESOLUTION_MAP[home_team]
                    elif away_score > home_score:
                        return RESOLUTION_MAP[away_team]
                elif game['Status'] == "Postponed":
                    return RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Canceled":
                    return RESOLUTION_MAP["50-50"]
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return RESOLUTION_MAP["Too early to resolve"]

    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    result = fetch_game_result()
    print(f"recommendation: {result}")