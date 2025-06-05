import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Function to make API requests
def make_api_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return None

# Function to find the game and determine the outcome
def resolve_mlb_game(date, team1, team2):
    # Format the date for the API request
    game_date = datetime.strptime(date, "%Y-%m-%d").date()
    formatted_date = game_date.strftime("%Y-%m-%d")

    # API endpoint
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{formatted_date}"

    # Make the API request
    games = make_api_request(url)
    if not games:
        return "p4"  # Unable to resolve due to API error

    # Search for the specific game
    for game in games:
        if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
            if game['Status'] == "Final":
                # Determine the winner
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return "p1" if game['HomeTeam'] == team1 else "p2"
                else:
                    return "p2" if game['HomeTeam'] == team2 else "p1"
            elif game['Status'] == "Canceled":
                return "p3"
            elif game['Status'] == "Postponed":
                # Check if the game is rescheduled within the next day
                next_day = (game_date + timedelta(days=1)).strftime("%Y-%m-%d")
                return resolve_mlb_game(next_day, team1, team2)
            else:
                return "p4"  # Game not final or postponed without reschedule
    return "p4"  # Game not found on the specified date

# Main function to run the resolver
if __name__ == "__main__":
    # Game details
    game_date = "2025-06-04"
    team1 = "Los Angeles Dodgers"
    team2 = "New York Mets"

    # Resolve the game and print the recommendation
    recommendation = resolve_mlb_game(game_date, team1, team2)
    print(f"recommendation: {recommendation}")