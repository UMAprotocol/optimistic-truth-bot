import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
UEFA_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")  # Assuming UEFA API uses the same key as NHL for this example

# Constants
MATCH_DATE = "2025-05-31"
PLAYER_NAME = "Goncalo Ramos"
TEAMS = ["Paris Saint-Germain", "Inter Milan"]
FINAL_DATE = datetime.strptime("2025-12-31 23:59", "%Y-%m-%d %H:%M")

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": UEFA_API_KEY}

# URL for UEFA Champions League data (example endpoint)
UEFA_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate"

def fetch_match_data(date):
    """ Fetch match data from UEFA API """
    url = f"{UEFA_ENDPOINT}/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def check_player_goals(match_data, player_name):
    """ Check if the specified player scored in the match """
    for match in match_data:
        if match['HomeTeam'] in TEAMS and match['AwayTeam'] in TEAMS:
            players = match['Players']
            for player in players:
                if player['Name'] == player_name and player['Goals'] > 0:
                    return True
    return False

def resolve_market():
    """ Resolve the market based on the match data and player performance """
    current_time = datetime.now()
    if current_time > FINAL_DATE:
        return "recommendation: p3"  # Market resolves to 50-50 if not completed by end of 2025

    match_data = fetch_match_data(MATCH_DATE)
    if not match_data:
        return "recommendation: p4"  # Unable to fetch data or match not found

    if check_player_goals(match_data, PLAYER_NAME):
        return "recommendation: p2"  # Player scored, market resolves to Yes
    else:
        return "recommendation: p1"  # Player did not score, market resolves to No

if __name__ == "__main__":
    result = resolve_market()
    print(result)