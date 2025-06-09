import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants
DATE = "2025-06-06"
TEAM1 = "Kansas City Royals"
TEAM2 = "Chicago White Sox"
GAME_TIME = "19:40:00"

# API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to make API requests
def make_api_request(date):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}{formatted_date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            # Fallback to proxy endpoint
            response = requests.get(PROXY_ENDPOINT, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

# Function to determine the outcome of the game
def determine_outcome(games, team1, team2, game_time):
    for game in games:
        if game['HomeTeam'] == team1 and game['AwayTeam'] == team2:
            if game['DateTime'][-8:] == game_time:
                if game['Status'] == "Final":
                    if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                        return "p2"  # Royals win
                    elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                        return "p1"  # White Sox win
                elif game['Status'] == "Canceled":
                    return "p3"  # Game canceled
                elif game['Status'] == "Postponed":
                    return "p4"  # Game postponed
    return "p4"  # No data available or game not yet played

# Main function to run the program
def main():
    games = make_api_request(DATE)
    if games:
        result = determine_outcome(games, TEAM1, TEAM2, GAME_TIME)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p4")  # Unable to retrieve data

if __name__ == "__main__":
    main()