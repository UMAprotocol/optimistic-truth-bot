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
GAME_DATE = "2025-05-31"
TEAM1 = "STL"  # St. Louis Cardinals
TEAM2 = "TEX"  # Texas Rangers

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find the game and determine the outcome
def resolve_game():
    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, f"GamesByDate/{GAME_DATE}")
    if not games:
        # Fallback to primary endpoint
        games = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{GAME_DATE}")
    
    if games is None:
        return "recommendation: p4"  # Unable to retrieve data

    for game in games:
        if game['HomeTeam'] == TEAM1 and game['AwayTeam'] == TEAM2 or \
           game['HomeTeam'] == TEAM2 and game['AwayTeam'] == TEAM1:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                
                if winner == TEAM1:
                    return "recommendation: p2"  # Cardinals win
                else:
                    return "recommendation: p1"  # Rangers win
            elif game['Status'] == "Canceled":
                return "recommendation: p3"  # Game canceled
            elif game['Status'] == "Postponed":
                # Check if the game is rescheduled within the season
                future_games = make_request(PRIMARY_ENDPOINT, f"Games/{datetime.now().year}")
                if any(g['GameID'] == game['GameID'] for g in future_games):
                    return "recommendation: p4"  # Game postponed but rescheduled
                else:
                    return "recommendation: p3"  # Game postponed and not rescheduled
            else:
                return "recommendation: p4"  # Game not final yet
    return "recommendation: p4"  # No matching game found

# Main execution
if __name__ == "__main__":
    result = resolve_game()
    print(result)