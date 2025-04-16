import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants
RESOLUTION_MAP = {
    "New York Mets": "p2",
    "Minnesota Twins": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def fetch_game_result():
    url = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/2025-04-14"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == "MIN" and game['AwayTeam'] == "NYM":
                if game['Status'] == "Final":
                    if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                        return "recommendation: " + RESOLUTION_MAP["Minnesota Twins"]
                    elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
                        return "recommendation: " + RESOLUTION_MAP["New York Mets"]
                elif game['Status'] == "Postponed":
                    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Canceled":
                    return "recommendation: " + RESOLUTION_MAP["50-50"]
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Main function to execute the script
if __name__ == "__main__":
    result = fetch_game_result()
    print(result)