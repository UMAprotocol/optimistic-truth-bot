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

# URL for UEFA Champions League data (example endpoint, adjust as necessary)
UEFA_ENDPOINT = "https://api.sportsdata.io/v3/soccer/scores/json/GamesByDate/{date}"

def fetch_match_data(date):
    url = UEFA_ENDPOINT.format(date=date)
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def check_player_goals(match_data, player_name):
    for match in match_data:
        if match['HomeTeamName'] in TEAMS and match['AwayTeamName'] in TEAMS:
            # Assuming the structure contains player stats
            for player in match['PlayerStats']:
                if player['Name'] == player_name and player['Goals'] > 0:
                    return True
    return False

def resolve_market():
    today = datetime.now()
    if today > FINAL_DATE:
        return "recommendation: p3"  # Market resolves to 50-50 if not completed by end of 2025

    match_data = fetch_match_data(MATCH_DATE)
    if not match_data:
        return "recommendation: p4"  # Unable to fetch data or no data available

    if check_player_goals(match_data, PLAYER_NAME):
        return "recommendation: p2"  # Player scored more than 0.5 goals
    else:
        return "recommendation: p1"  # Player did not score

if __name__ == "__main__":
    result = resolve_market()
    print(result)