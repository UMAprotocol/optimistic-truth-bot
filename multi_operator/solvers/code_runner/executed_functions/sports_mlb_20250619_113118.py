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

# Function to find the game and determine the outcome
def find_game_and_determine_outcome(date_str):
    formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = PRIMARY_ENDPOINT + formatted_date
    games = make_request(url, HEADERS)
    
    if games is None:
        print("Failed to retrieve data from primary endpoint, trying proxy...")
        games = make_request(PROXY_ENDPOINT, HEADERS)
        if games is None:
            return "p4"  # Unable to retrieve data

    for game in games:
        if game['AwayTeam'] == "Felix Auger-Aliassime" and game['HomeTeam'] == "Karen Khachanov":
            if game['Status'] == "Final":
                if game['AwayTeamRuns'] > game['HomeTeamRuns']:
                    return "p2"  # Auger-Aliassime wins
                elif game['AwayTeamRuns'] < game['HomeTeamRuns']:
                    return "p1"  # Khachanov wins
            elif game['Status'] in ["Canceled", "Postponed"]:
                return "p3"  # Game canceled or postponed
            else:
                return "p4"  # Game not yet completed or other statuses
    return "p4"  # No matching game found or game not yet played

# Main execution function
if __name__ == "__main__":
    match_date = "2025-06-19"
    recommendation = find_game_and_determine_outcome(match_date)
    print(f"recommendation: {recommendation}")