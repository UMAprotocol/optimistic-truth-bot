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

# Constants for the event
EVENT_DATE = "2025-06-16"
MATCH_TIME = "15:00"  # 3:00 PM ET
TEAMS = ["Chelsea", "LAFC"]
RESOLUTION_MAP = {
    "Yes": "p2",  # More than 3.5 goals
    "No": "p1",   # 3.5 goals or less
    "Unknown": "p3"  # Canceled or postponed
}

# Function to get match data
def get_match_data(date):
    url = f"https://api.sportsdata.io/v3/soccer/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Function to evaluate the match outcome
def evaluate_match(matches):
    for match in matches:
        if match['HomeTeamName'] in TEAMS and match['AwayTeamName'] in TEAMS:
            if match['DateTime'][:10] == EVENT_DATE and match['Status'] == "Scheduled":
                total_goals = match['HomeTeamScore'] + match['AwayTeamScore']
                if total_goals > 3.5:
                    return RESOLUTION_MAP["Yes"]
                else:
                    return RESOLUTION_MAP["No"]
            elif match['Status'] in ["Canceled", "Postponed"]:
                return RESOLUTION_MAP["Unknown"]
    return RESOLUTION_MAP["Unknown"]

# Main function to run the program
def main():
    matches = get_match_data(EVENT_DATE)
    if matches:
        result = evaluate_match(matches)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p3")  # Assume unknown if no data is retrieved

if __name__ == "__main__":
    main()