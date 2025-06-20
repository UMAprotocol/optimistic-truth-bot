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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check the match and calculate the total goals
def check_match_and_goals(date, team1, team2):
    games_today = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date}")
    if games_today:
        for game in games_today:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
               (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                if game['Status'] == "Final":
                    total_goals = game['HomeTeamRuns'] + game['AwayTeamRuns']
                    return total_goals
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return "Canceled or Postponed"
    return "No Match Found"

# Main function to resolve the market
def resolve_market():
    match_date = "2025-06-16"
    team1 = "Flamengo"
    team2 = "Esperance Sportive de Tunis"
    result = check_match_and_goals(match_date, team1, team2)
    
    if isinstance(result, int):
        if result > 2.5:
            print("recommendation: p2")  # Yes, more than 2.5 goals
        else:
            print("recommendation: p1")  # No, not more than 2.5 goals
    elif result == "Canceled or Postponed":
        print("recommendation: p1")      # No, as the match was canceled or postponed
    else:
        print("recommendation: p3")      # Unknown/50-50, no match found

# Run the market resolver
if __name__ == "__main__":
    resolve_market()