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

# Function to perform API requests
def get_api_response(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return None

# Function to find the game and determine the outcome
def resolve_game(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{formatted_date}"
    games = get_api_response(url)
    
    if games is None:
        return "p4"  # Unable to retrieve data

    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return "p2" if game["HomeTeam"] == team1 else "p1"
                else:
                    return "p1" if game["AwayTeam"] == team1 else "p2"
            elif game["Status"] == "Canceled":
                return "p3"
            elif game["Status"] == "Postponed":
                # Check if the game is rescheduled within the next two days
                reschedule_date = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=2)).strftime("%Y-%m-%d")
                return resolve_game(reschedule_date, team1, team2)
            else:
                return "p4"  # Game not completed yet
    return "p4"  # Game not found on the specified date

# Main execution function
def main():
    # Game details
    game_date = "2025-06-17"
    team1 = "PHI"  # Philadelphia Phillies
    team2 = "MIA"  # Miami Marlins

    # Resolve the game outcome
    result = resolve_game(game_date, team1, team2)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()