import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    if not api_key:
        return "recommendation: p4"  # API key not found, cannot resolve

    url = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-14"
    headers = {
        "Ocp-Apim-Subscription-Key": api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()
    except requests.RequestException:
        return "recommendation: p4"  # API error or connection issue

    RESOLUTION_MAP = {
        "NYR": "p2",  # New York Rangers
        "FLA": "p1",  # Florida Panthers
        "50-50": "p3",
        "Too early to resolve": "p4",
    }

    for game in games:
        if game['HomeTeam'] == "NYR" and game['AwayTeam'] == "FLA" or game['HomeTeam'] == "FLA" and game['AwayTeam'] == "NYR":
            if game['Status'] == "Final":
                if game['HomeTeam'] == "NYR" and game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "recommendation: " + RESOLUTION_MAP["NYR"]
                elif game['AwayTeam'] == "NYR" and game['AwayTeamScore'] > game['HomeTeamScore']:
                    return "recommendation: " + RESOLUTION_MAP["NYR"]
                elif game['HomeTeam'] == "FLA" and game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "recommendation: " + RESOLUTION_MAP["FLA"]
                elif game['AwayTeam'] == "FLA" and game['AwayTeamScore'] > game['HomeTeamScore']:
                    return "recommendation: " + RESOLUTION_MAP["FLA"]
            elif game['Status'] == "Postponed":
                return "recommendation: p4"  # Game postponed, too early to resolve
            elif game['Status'] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
    return "recommendation: p4"  # No matching game found or too early to resolve

# Example usage
result = fetch_nhl_game_result()
print(result)