import os
import requests
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
def make_request(date):
    try:
        response = requests.get(f"{PROXY_ENDPOINT}/{date}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.RequestException, requests.exceptions.HTTPError):
        try:
            response = requests.get(f"{PRIMARY_ENDPOINT}{date}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to retrieve data from both endpoints: {str(e)}")
            return None

# Function to determine the outcome based on the game data
def determine_outcome(games):
    for game in games:
        if "Final" in game['Status']:
            if game['AwayTeamRuns'] > game['HomeTeamRuns']:
                return "p1"  # Away team wins
            elif game['HomeTeamRuns'] > game['AwayTeamRuns']:
                return "p2"  # Home team wins
            else:
                return "p3"  # Tie
    return "p4"  # No final games found or games in progress

# Main function to execute the logic
def main():
    date = "2025-04-23"  # Example date
    games = make_request(date)
    if games:
        result = determine_outcome(games)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p4")  # Unable to retrieve data

if __name__ == "__main__":
    main()