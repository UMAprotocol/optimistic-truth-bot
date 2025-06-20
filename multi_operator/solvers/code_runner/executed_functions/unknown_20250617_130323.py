import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
HSBC_CHAMPIONSHIPS_URL = "https://www.lta.org.uk/fan-zone/international/hsbc-championships/"
MATCH_DATE = "2025-06-17"
MATCH_TIME = "10:00 AM ET"
PLAYER1 = "Carlos Alcaraz"
PLAYER2 = "Alejandro Davidovich Fokina"
DEADLINE_DATE = "2025-06-24"

# Headers for requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def fetch_match_data():
    try:
        response = requests.get(HSBC_CHAMPIONSHIPS_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def analyze_match_result(data):
    if not data:
        return "p3"  # Unknown or error, resolve as 50-50

    # Extract relevant match information
    for match in data.get('matches', []):
        if (match['date'] == MATCH_DATE and match['time'] == MATCH_TIME and
            PLAYER1 in match['players'] and PLAYER2 in match['players']):
            if match['status'] in ["canceled", "postponed"]:
                return "p3"  # Match canceled or postponed, resolve as 50-50
            winner = match.get('winner')
            if winner == PLAYER1:
                return "p2"  # Alcaraz wins
            elif winner == PLAYER2:
                return "p1"  # Fokina wins

    # If no match found or no winner determined
    current_date = datetime.now()
    deadline_date = datetime.strptime(DEADLINE_DATE, "%Y-%m-%d")
    if current_date > deadline_date:
        return "p3"  # Past the deadline without a result, resolve as 50-50
    return "p4"  # Match not yet played or in progress

if __name__ == "__main__":
    match_data = fetch_match_data()
    recommendation = analyze_match_result(match_data)
    print(f"recommendation: {recommendation}")