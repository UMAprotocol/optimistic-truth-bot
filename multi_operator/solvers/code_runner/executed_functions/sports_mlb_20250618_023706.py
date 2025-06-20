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

# Function to make GET requests to the API
def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_outcome(date, team1, team2):
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    games = get_data(url)
    if games:
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
               (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                if game['Status'] == "Final":
                    if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                        return "Royals" if game['HomeTeam'] == team1 else "Rangers"
                    else:
                        return "Rangers" if game['AwayTeam'] == team1 else "Royals"
                elif game['Status'] == "Postponed":
                    return "Postponed"
                elif game['Status'] == "Canceled":
                    return "Canceled"
    return "Data not available"

# Main function to run the program
def main():
    date = "2025-06-17"
    team1 = "Kansas City Royals"
    team2 = "Texas Rangers"
    result = find_game_and_outcome(date, team1, team2)
    if result == "Royals":
        print("recommendation: p2")
    elif result == "Rangers":
        print("recommendation: p1")
    elif result == "Postponed":
        print("The game is postponed. Please check later.")
    elif result == "Canceled":
        print("recommendation: p3")
    else:
        print(result)

if __name__ == "__main__":
    main()