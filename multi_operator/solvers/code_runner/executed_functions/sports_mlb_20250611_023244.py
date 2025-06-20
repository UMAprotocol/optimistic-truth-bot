import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
DATE = "2025-06-10"
TEAM1 = "MIL"  # Milwaukee Brewers
TEAM2 = "ATL"  # Atlanta Braves

# Function to get data from API
def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome():
    date_formatted = datetime.strptime(DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date_formatted}"
    games = get_data(url)
    
    if games is None:
        return "p4"  # Unable to resolve due to data fetch error

    for game in games:
        if game['HomeTeam'] == TEAM1 and game['AwayTeam'] == TEAM2 or \
           game['HomeTeam'] == TEAM2 and game['AwayTeam'] == TEAM1:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return "p1" if game['HomeTeam'] == TEAM1 else "p2"
                else:
                    return "p2" if game['HomeTeam'] == TEAM1 else "p1"
            elif game['Status'] == "Canceled":
                return "p3"
            elif game['Status'] == "Postponed":
                # Market remains open, but we return p4 since we cannot resolve now
                return "p4"
            else:
                # Game is not yet final
                return "p4"
    return "p4"  # No game found or game does not match criteria

# Main execution
if __name__ == "__main__":
    recommendation = find_game_and_determine_outcome()
    print(f"recommendation: {recommendation}")