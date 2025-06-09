import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
HLTV_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")

# Constants for the event
EVENT_DATE = "2025-06-08"
TEAM1 = "TYLOO"
TEAM2 = "Lynn Vision"
HLTV_EVENT_ID = "7902"

# HLTV API URL
HLTV_URL = "https://api.sportsdata.io/v3/cbb/scores/json/GamesByDate"

# Headers for API request
HEADERS = {
    "Ocp-Apim-Subscription-Key": HLTV_API_KEY
}

def fetch_match_results(date, event_id):
    """
    Fetch match results from HLTV for a specific date and event.
    """
    response = requests.get(f"{HLTV_URL}/{date}", headers=HEADERS)
    if response.status_code == 200:
        matches = response.json()
        for match in matches:
            if match.get('EventId') == event_id:
                return match
    return None

def determine_winner(match):
    """
    Determine the winner of the match based on the scores.
    """
    if not match:
        return "p3"  # Match not found, assume canceled or postponed
    if match['Status'] == 'Final':
        team1_score = match['HomeTeamScore'] if match['HomeTeam'] == TEAM1 else match['AwayTeamScore']
        team2_score = match['HomeTeamScore'] if match['HomeTeam'] == TEAM2 else match['AwayTeamScore']
        if team1_score > team2_score:
            return "p2"  # TEAM1 wins
        elif team2_score > team1_score:
            return "p1"  # TEAM2 wins
        else:
            return "p3"  # Tie
    else:
        return "p3"  # Non-final status, assume postponed or canceled

def main():
    """
    Main function to determine the outcome of the match.
    """
    match = fetch_match_results(EVENT_DATE, HLTV_EVENT_ID)
    result = determine_winner(match)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()