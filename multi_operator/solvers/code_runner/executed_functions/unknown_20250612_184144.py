import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
HLTV_EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
MATCH_DATE = "2025-06-12"
MATCH_TIME = "14:45"  # 2:45 PM ET in 24-hour format
TEAM1 = "Nemiga"
TEAM2 = "Natus Vincere"
DEADLINE_DATE = "2025-06-28"

# Load API key from environment
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def fetch_match_data():
    """Fetches match data from HLTV."""
    response = requests.get(HLTV_EVENT_URL, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} {response.reason}")

def parse_match_data(data):
    """Parses match data to determine the outcome."""
    current_date = datetime.utcnow().date()
    match_datetime = datetime.strptime(f"{MATCH_DATE} {MATCH_TIME}", "%Y-%m-%d %H:%M")
    deadline_date = datetime.strptime(DEADLINE_DATE, "%Y-%m-%d").date()

    # Check if current date is before the match date
    if current_date < match_datetime.date():
        return "p4"  # Match has not occurred yet

    # Check if current date is past the deadline
    if current_date > deadline_date:
        return "p3"  # Match delayed beyond deadline

    # Find the specific match
    for match in data['matches']:
        if match['team1']['name'] == TEAM1 and match['team2']['name'] == TEAM2:
            if match['result']['score1'] > match['result']['score2']:
                return "p1"  # Team1 wins
            elif match['result']['score1'] < match['result']['score2']:
                return "p2"  # Team2 wins
            else:
                return "p3"  # Tie or error in data

    # If no specific match found or other issues
    return "p3"  # Resolve as unknown/50-50

def main():
    try:
        match_data = fetch_match_data()
        outcome = parse_match_data(match_data)
        print(f"recommendation: {outcome}")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("recommendation: p3")  # Resolve as unknown/50-50 in case of errors

if __name__ == "__main__":
    main()