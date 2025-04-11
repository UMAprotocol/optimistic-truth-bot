import requests
from dotenv import load_dotenv
import os
import datetime

# Load environment variables
load_dotenv()

# Constants for the game
TEAM_A = "Brooklyn Nets"
TEAM_B = "Atlanta Hawks"
GAME_DATE = "2025-04-10"
GAME_TIME = "19:30:00"  # 7:30 PM ET in 24-hour format

# API Key for Sports Data IO
API_KEY = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')

# API Endpoint
API_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}"

def fetch_game_data(date):
    """
    Fetches game data for a specific date from the Sports Data IO API.
    """
    headers = {
        'Ocp-Apim-Subscription-Key': API_KEY
    }
    response = requests.get(API_ENDPOINT.format(date=date), headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def analyze_game_data(games):
    """
    Analyzes the list of games to find the outcome of the specific game between TEAM_A and TEAM_B.
    """
    for game in games:
        if game['HomeTeam'] in [TEAM_A, TEAM_B] and game['AwayTeam'] in [TEAM_A, TEAM_B]:
            if game['Status'] == "Final":
                if game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "Hawks" if game['HomeTeam'] == TEAM_B else "Nets"
                else:
                    return "Nets" if game['HomeTeam'] == TEAM_A else "Hawks"
            elif game['Status'] == "Postponed":
                return "Postponed"
            elif game['Status'] == "Canceled":
                return "Canceled"
    return "No Game Found"

def main():
    """
    Main function to determine the outcome of the game.
    """
    full_date_time = f"{GAME_DATE}T{GAME_TIME}"
    current_time = datetime.datetime.utcnow().isoformat()
    
    # Check if the game is in the future
    if current_time < full_date_time:
        print("recommendation: p4")
        return
    
    games = fetch_game_data(GAME_DATE)
    if games is None:
        print("Error fetching data")
        return
    
    result = analyze_game_data(games)
    if result == "Hawks":
        print("recommendation: p2")
    elif result == "Nets":
        print("recommendation: p1")
    elif result == "Postponed":
        print("recommendation: p4")
    elif result == "Canceled":
        print("recommendation: p3")
    else:
        print("recommendation: p4")

if __name__ == "__main__":
    main()