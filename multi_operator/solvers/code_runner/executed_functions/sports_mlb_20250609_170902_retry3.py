import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not MLB_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": MLB_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Pirates": "p2",  # Pittsburgh Pirates win
    "Padres": "p1",   # San Diego Padres win
    "Canceled": "p3", # Game canceled
    "Postponed": "p4" # Game postponed or in progress
}

def get_game_data(date):
    """ Fetch game data from the API """
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
    
    try:
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Proxy failed")
    except:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            response.raise_for_status()
    
    return response.json()

def analyze_game_data(games):
    """ Analyze game data to determine the outcome """
    for game in games:
        if game['HomeTeam'] == 'SD' and game['AwayTeam'] == 'PIT':
            if game['Status'] == 'Final':
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP['Padres']
                else:
                    return RESOLUTION_MAP['Pirates']
            elif game['Status'] == 'Canceled':
                return RESOLUTION_MAP['Canceled']
            elif game['Status'] == 'Postponed':
                return RESOLUTION_MAP['Postponed']
    return "p4"  # No relevant game found or still in progress

def main():
    # Define the date of the game
    game_date = "2025-06-01"
    
    # Fetch game data
    games = get_game_data(game_date)
    
    # Analyze the game data to determine the outcome
    result = analyze_game_data(games)
    
    # Print the recommendation
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()