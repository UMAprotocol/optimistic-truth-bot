import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
UEFA_NATIONS_LEAGUE_URL = "https://www.uefa.com/uefanationsleague/"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
MATCH_DATE = "2025-06-08"
MATCH_TIME = "15:00"  # 3:00 PM ET
PLAYER_NAME = "Gonçalo Ramos"
TEAMS = {"Portugal", "Spain"}

# Resolution conditions
RESOLUTION_MAP = {
    "Yes": "p2",  # Gonçalo Ramos scores more than 0.5 goals
    "No": "p1",   # Gonçalo Ramos does not score more than 0.5 goals
    "50-50": "p3" # Match not completed by the end of 2025
}

def fetch_match_data():
    """Fetches data from UEFA Nations League API."""
    response = requests.get(UEFA_NATIONS_LEAGUE_URL, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Failed to fetch data from UEFA Nations League")

def parse_match_data(data):
    """Parses match data to determine if Gonçalo Ramos scored a goal."""
    for match in data.get('matches', []):
        if match['date'].startswith(MATCH_DATE) and match['time'] == MATCH_TIME and match['teams'] == TEAMS:
            if datetime.now() < datetime.strptime(f"{MATCH_DATE} {MATCH_TIME}", "%Y-%m-%d %H:%M"):
                return "Too early to resolve"
            if match['status'] == 'completed':
                goals = match['player_goals'].get(PLAYER_NAME, 0)
                return "Yes" if goals > 0.5 else "No"
            else:
                return "50-50"
    return "No match found"

def main():
    try:
        match_data = fetch_match_data()
        result = parse_match_data(match_data)
        recommendation = RESOLUTION_MAP.get(result, "p4")
        print(f"recommendation: {recommendation}")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("recommendation: p4")

if __name__ == "__main__":
    main()