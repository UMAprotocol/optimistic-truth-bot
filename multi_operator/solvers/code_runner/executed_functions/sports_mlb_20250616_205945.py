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

# Function to check the match result
def check_match_result(date, team1, team2):
    games_today = make_request(PROXY_ENDPOINT, f"GamesByDate/{date}")
    if not games_today:
        games_today = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date}")
    
    if games_today:
        for game in games_today:
            if {game['HomeTeam'], game['AwayTeam']} == {team1, team2}:
                if game['Status'] == 'Final':
                    total_goals = game['HomeTeamRuns'] + game['AwayTeamRuns']
                    return "p2" if total_goals > 3.5 else "p1"
                elif game['Status'] in ['Canceled', 'Postponed']:
                    return "p1"
    return "p3"

# Main execution function
def main():
    match_date = "2025-06-16"
    team1 = "Chelsea"
    team2 = "LAFC"
    result = check_match_result(match_date, team1, team2)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()