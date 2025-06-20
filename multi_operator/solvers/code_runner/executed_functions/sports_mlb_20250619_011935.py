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

# Game details
GAME_DATE = "2025-06-18"
PHILLIES = "PHI"
MARLINS = "MIA"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error during request to {endpoint}/{path}: {str(e)}")
        return None

# Function to find the game and determine the outcome
def resolve_game():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date_formatted}")

    if not games_today:
        print("Failed to retrieve games data. Trying proxy...")
        games_today = make_request(PROXY_ENDPOINT, f"GamesByDate/{date_formatted}")

    if games_today:
        for game in games_today:
            if game['HomeTeam'] == MARLINS and game['AwayTeam'] == PHILLIES or \
               game['HomeTeam'] == PHILLIES and game['AwayTeam'] == MARLINS:
                if game['Status'] == 'Final':
                    home_score = game['HomeTeamRuns']
                    away_score = game['AwayTeamRuns']
                    if home_score > away_score:
                        return "p2" if game['HomeTeam'] == PHILLIES else "p1"
                    else:
                        return "p1" if game['HomeTeam'] == MARLINS else "p2"
                elif game['Status'] == 'Postponed':
                    return "Market remains open"
                elif game['Status'] == 'Canceled':
                    return "p3"
    return "p4"

# Main execution
if __name__ == "__main__":
    result = resolve_game()
    print(f"recommendation: {result}")