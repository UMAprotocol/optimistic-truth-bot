import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants
DATE = "2025-06-07"
TEAM1 = "Chicago White Sox"
TEAM2 = "Kansas City Royals"
GAME_TIME = "16:10:00"

# Function to get data from API
def get_data(url, params=None):
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome():
    date_time_str = f"{DATE}T{GAME_TIME}"
    date_time_obj = datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%S")
    games_url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{DATE}"
    games = get_data(games_url)

    if games is None:
        return "p4"  # Unable to fetch data

    for game in games:
        if game['DateTime'] == date_time_str:
            if game['Status'] == "Final":
                if game['AwayTeam'] == TEAM1 and game['AwayTeamRuns'] > game['HomeTeamRuns']:
                    return "p1"  # White Sox win
                elif game['HomeTeam'] == TEAM2 and game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return "p2"  # Royals win
                else:
                    return "p3"  # Tie or error in data
            elif game['Status'] in ["Canceled", "Postponed"]:
                return "p3"  # Game not completed
            else:
                return "p4"  # Game not final yet
    return "p4"  # No matching game found

# Main execution
if __name__ == "__main__":
    result = find_game_and_determine_outcome()
    print(f"recommendation: {result}")