import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    if not api_key:
        return "recommendation: p4"  # Unable to resolve due to missing API key

    url = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-14"
    headers = {
        "Ocp-Apim-Subscription-Key": api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()

        # Define the resolution map with NHL team abbreviations
        RESOLUTION_MAP = {
            "DAL": "p2",  # Dallas Stars
            "DET": "p1",  # Detroit Red Wings
            "50-50": "p3",
            "Too early to resolve": "p4",
        }

        for game in games:
            if game['HomeTeam'] == "DET" and game['AwayTeam'] == "DAL":
                if game['Status'] == "Final":
                    if game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP["DET"]
                    elif game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP["DAL"]
                elif game['Status'] == "Postponed":
                    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Canceled":
                    return "recommendation: " + RESOLUTION_MAP["50-50"]
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "recommendation: p4"  # Unable to resolve due to API error

# Example usage
result = fetch_nhl_game_result()
print(result)