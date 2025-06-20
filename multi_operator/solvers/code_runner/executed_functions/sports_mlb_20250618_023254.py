import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Function to perform GET requests
def get_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during requests to {url}: {str(e)}")
        return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{formatted_date}"
    games = get_request(url)
    if games:
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                if game['Status'] == "Final":
                    if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                        return "p1" if game['HomeTeam'] == team1 else "p2"
                    elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                        return "p2" if game['HomeTeam'] == team1 else "p1"
                elif game['Status'] == "Canceled":
                    return "p3"
                elif game['Status'] == "Postponed":
                    # Check for rescheduled game
                    new_date = datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)
                    return find_game_and_determine_outcome(new_date.strftime("%Y-%m-%d"), team1, team2)
    return "p4"

# Main function to run the program
if __name__ == "__main__":
    # Define the game details
    game_date = "2025-06-17"
    team1 = "BAL"  # Baltimore Orioles
    team2 = "TBR"  # Tampa Bay Rays

    # Determine the outcome
    result = find_game_and_determine_outcome(game_date, team1, team2)
    print(f"recommendation: {result}")