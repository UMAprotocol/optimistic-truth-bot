import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants
GAME_DATE = "2025-06-07"
TEAM1 = "Texas Rangers"
TEAM2 = "Washington Nationals"
RESOLUTION_MAP = {
    "Rangers": "p2",
    "Nationals": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Function to make GET requests to the API
def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to find the game and determine the outcome
def resolve_game():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date_formatted}"
    games = get_data(url)
    
    if not games:
        return RESOLUTION_MAP["Too early to resolve"]
    
    for game in games:
        if game["HomeTeam"] == TEAM1 and game["AwayTeam"] == TEAM2 or \
           game["HomeTeam"] == TEAM2 and game["AwayTeam"] == TEAM1:
            if game["Status"] == "Final":
                home_score = game["HomeTeamRuns"]
                away_score = game["AwayTeamRuns"]
                if home_score > away_score:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                
                if winner == TEAM1:
                    return RESOLUTION_MAP["Rangers"]
                else:
                    return RESOLUTION_MAP["Nationals"]
            elif game["Status"] == "Postponed":
                return RESOLUTION_MAP["Too early to resolve"]
            elif game["Status"] == "Canceled":
                return RESOLUTION_MAP["50-50"]
    
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    result = resolve_game()
    print(f"recommendation: {result}")