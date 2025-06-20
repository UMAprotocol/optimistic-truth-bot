import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
EVENT_DATE = "2025-06-19"
MATCH_TIME = "06:00 AM ET"
PLAYER1 = "Denis Shapovalov"
PLAYER2 = "Flavio Cobolli"
TOURNAMENT = "Terra Wortmann Open"
ROUND = "Round 2"
RESOLUTION_MAP = {
    "Shapovalov": "p2",
    "Cobolli": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Helper functions
def get_match_result():
    url = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/" + EVENT_DATE
    headers = {"Ocp-Apim-Subscription-Key": API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if game['Date'][:10] == EVENT_DATE and PLAYER1 in game['Players'] and PLAYER2 in game['Players']:
                if game['Status'] == "Final":
                    winner = game['Winner']
                    return RESOLUTION_MAP.get(winner, "50-50")
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return RESOLUTION_MAP["50-50"]
        return RESOLUTION_MAP["Too early to resolve"]
    else:
        raise Exception("Failed to fetch data from API")

# Main execution
if __name__ == "__main__":
    current_date = datetime.now().strftime("%Y-%m-%d")
    if current_date > EVENT_DATE:
        result = get_match_result()
    else:
        result = RESOLUTION_MAP["Too early to resolve"]
    print("recommendation:", result)