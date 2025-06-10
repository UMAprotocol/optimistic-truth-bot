import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Game details extracted from the question
GAME_DATE = "2025-05-30"
TEAM1 = "Gujarat Titans"
TEAM2 = "Mumbai Indians"

# Resolution map based on the outcomes
RESOLUTION_MAP = {
    TEAM1: "p2",  # Gujarat Titans win
    TEAM2: "p1",  # Mumbai Indians win
    "Canceled": "p3",  # Game canceled
    "Postponed": "p4",  # Game postponed
    "Unknown": "p4"  # Unknown or not enough data
}

def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def resolve_market():
    # Convert game date to the required format
    game_date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    
    # Construct URL to fetch games by date
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{game_date_formatted}"
    
    # Fetch data from the primary endpoint
    games = get_data(url)
    if not games:
        print("Failed to retrieve data from primary endpoint, trying proxy...")
        games = get_data(PROXY_ENDPOINT)
    
    if not games:
        return "recommendation: " + RESOLUTION_MAP["Unknown"]
    
    # Check each game to find the match
    for game in games:
        if game['HomeTeam'] == TEAM1 and game['AwayTeam'] == TEAM2 or \
           game['HomeTeam'] == TEAM2 and game['AwayTeam'] == TEAM1:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                return "recommendation: " + RESOLUTION_MAP.get(winner, RESOLUTION_MAP["Unknown"])
            elif game['Status'] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["Canceled"]
            elif game['Status'] == "Postponed":
                return "recommendation: " + RESOLUTION_MAP["Postponed"]
    
    return "recommendation: " + RESOLUTION_MAP["Unknown"]

# Execute the market resolution function
if __name__ == "__main__":
    result = resolve_market()
    print(result)