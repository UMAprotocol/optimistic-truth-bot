import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Define the resolution map using team abbreviations
RESOLUTION_MAP = {
    "VGK": "p2",  # Vegas Golden Knights
    "CGY": "p1",  # Calgary Flames
    "50-50": "p3",
    "Too early to resolve": "p4",
}

def fetch_nhl_game_result():
    # Define the API endpoint
    url = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-15"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }

    try:
        # Make the API request
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()

        # Search for the specific game
        for game in games:
            if game['HomeTeam'] == "VGK" and game['AwayTeam'] == "CGY":
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return "recommendation: " + RESOLUTION_MAP["VGK"]
                    elif away_score > home_score:
                        return "recommendation: " + RESOLUTION_MAP["CGY"]
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