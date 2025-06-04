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
def find_game_and_determine_outcome(date):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = PRIMARY_ENDPOINT + formatted_date
    games = make_request(url, HEADERS)
    if games:
        for game in games:
            if (game['HomeTeam'] == 'Keys' and game['AwayTeam'] == 'Gauff') or (game['HomeTeam'] == 'Gauff' and game['AwayTeam'] == 'Keys'):
                if game['Status'] == 'Final':
                    if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                        return "p1" if game['HomeTeam'] == 'Gauff' else "p2"
                    elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                        return "p1" if game['AwayTeam'] == 'Gauff' else "p2"
                elif game['Status'] in ['Canceled', 'Postponed']:
                    return "p3"
    return "p4"

# Main function to run the program
def main():
    match_date = "2025-06-04"
    result = find_game_and_determine_outcome(match_date)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()