import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check the game status and resolve the market
def check_game_status(date):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = PRIMARY_ENDPOINT + formatted_date
    games = make_request(url, HEADERS)
    
    if games is None:
        print("Failed to retrieve data from primary endpoint, trying proxy...")
        games = make_request(PROXY_ENDPOINT, HEADERS)
        if games is None:
            return "p3"  # Unknown or error state

    for game in games:
        if game['HomeTeam'] == "BAY" and game['AwayTeam'] == "AUC":
            if game['Status'] == "Final":
                total_goals = game['HomeTeamRuns'] + game['AwayTeamRuns']
                if total_goals > 4.5:
                    return "p2"  # Yes, more than 4.5 goals
                else:
                    return "p1"  # No, not more than 4.5 goals
            elif game['Status'] in ["Canceled", "Postponed"]:
                return "p1"  # No, game not played or postponed
    return "p3"  # If no matching game found or other issues

# Main execution function
if __name__ == "__main__":
    match_date = "2025-06-15"
    recommendation = check_game_status(match_date)
    print(f"recommendation: {recommendation}")