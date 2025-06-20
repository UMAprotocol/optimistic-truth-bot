import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants for the match
MATCH_DATE = "2025-06-15"
TEAM1 = "Bayern Munich"
TEAM2 = "Auckland City"
GOAL_THRESHOLD = 4.5

# Function to get match data
def get_match_data(date):
    url = f"https://api.sportsdata.io/v3/soccer/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Function to analyze match data
def analyze_match_data(match_data, team1, team2, goal_threshold):
    for match in match_data:
        if match['HomeTeamName'] == team1 and match['AwayTeamName'] == team2:
            total_goals = match['HomeTeamScore'] + match['AwayTeamScore']
            if total_goals > goal_threshold:
                return "p2"  # Yes, more than 4.5 goals
            else:
                return "p1"  # No, not more than 4.5 goals
    return "p3"  # Match not found or data insufficient

# Main function to resolve the market
def resolve_market():
    match_data = get_match_data(MATCH_DATE)
    if match_data:
        result = analyze_match_data(match_data, TEAM1, TEAM2, GOAL_THRESHOLD)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p3")  # Unable to retrieve data

# Run the resolver
if __name__ == "__main__":
    resolve_market()