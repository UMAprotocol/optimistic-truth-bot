import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Define the resolution map using team abbreviations
RESOLUTION_MAP = {
    "FLA": "p2",  # Florida Panthers
    "TBL": "p1",  # Tampa Bay Lightning
    "50-50": "p3",
    "Too early to resolve": "p4",
}

def fetch_nhl_game_result():
    # API endpoint setup
    url = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-15"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()

        # Search for the specific game
        for game in games:
            if game['HomeTeam'] == "FLA" and game['AwayTeam'] == "TBL" or game['HomeTeam'] == "TBL" and game['AwayTeam'] == "FLA":
                if game['Status'] == "Final":
                    if game['HomeTeam'] == "FLA" and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP["FLA"]
                    elif game['AwayTeam'] == "FLA" and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP["FLA"]
                    else:
                        return "recommendation: " + RESOLUTION_MAP["TBL"]
                elif game['Status'] == "Postponed":
                    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Canceled":
                    return "recommendation: " + RESOLUTION_MAP["50-50"]
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Execute the function and print the result
result = fetch_nhl_game_result()
print(result)