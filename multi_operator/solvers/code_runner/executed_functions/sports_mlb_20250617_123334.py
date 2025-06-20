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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy/mlb/scores/json/GamesByDate/"

# Date and teams for the match
MATCH_DATE = "2025-06-17"
TEAM1 = "De Minaur"
TEAM2 = "Lehecka"

# Function to make API requests
def make_request(date):
    url = f"{PRIMARY_ENDPOINT}{date}"
    proxy_url = f"{PROXY_ENDPOINT}{date}"
    try:
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        if not response.ok:
            response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to determine the outcome of the match
def determine_outcome(games, team1, team2):
    for game in games:
        if team1 in game['HomeTeamName'] and team2 in game['AwayTeamName']:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return "p2"  # De Minaur wins
                else:
                    return "p1"  # Lehecka wins
            elif game['Status'] in ["Canceled", "Postponed"]:
                return "p3"  # 50-50
    return "p4"  # Too early or no data

# Main function to run the program
def main():
    games = make_request(MATCH_DATE)
    if games:
        result = determine_outcome(games, TEAM1, TEAM2)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p4")  # No data available

if __name__ == "__main__":
    main()