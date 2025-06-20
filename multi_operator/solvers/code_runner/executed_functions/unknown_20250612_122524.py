import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if endpoint == PROXY_ENDPOINT:
            print(f"Falling back to primary endpoint due to error: {e}")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"Error accessing API: {e}")
            return None

# Function to find the game result
def find_game_result(date, player1, player2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PROXY_ENDPOINT, f"/scores/json/GamesByDate/{formatted_date}")

    if games_today:
        for game in games_today:
            if player1 in game['HomeTeam'] or player1 in game['AwayTeam']:
                if player2 in game['HomeTeam'] or player2 in game['AwayTeam']:
                    if game['Status'] == "Final":
                        home_team_won = game['HomeTeamRuns'] > game['AwayTeamRuns']
                        if (game['HomeTeam'] == player1 and home_team_won) or (game['AwayTeam'] == player1 and not home_team_won):
                            return "p1"
                        else:
                            return "p2"
                    elif game['Status'] in ["Canceled", "Postponed"]:
                        return "p3"
                    else:
                        return "p4"
    return "p4"

# Main function to execute the logic
if __name__ == "__main__":
    # Define the match details
    match_date = "2025-06-12"
    player1 = "Giovanni Mpetshi Perricard"
    player2 = "Felix Auger-Aliassime"

    # Get the game result and print the recommendation
    result = find_game_result(match_date, player1, player2)
    print(f"recommendation: {result}")