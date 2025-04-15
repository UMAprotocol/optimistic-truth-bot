import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    url = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-14"
    headers = {
        "Ocp-Apim-Subscription-Key": api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == "VAN" and game['AwayTeam'] == "SJS":
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return resolve_market("VAN")
                    elif away_score > home_score:
                        return resolve_market("SJS")
                elif game['Status'] == "Postponed":
                    return resolve_market("Too early to resolve")
                elif game['Status'] == "Canceled":
                    return resolve_market("50-50")
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return resolve_market("Too early to resolve")

    return resolve_market("Too early to resolve")

def resolve_market(team):
    RESOLUTION_MAP = {
        "VAN": "p1",  # Canucks
        "SJS": "p2",  # Sharks
        "50-50": "p3",
        "Too early to resolve": "p4",
    }
    return "recommendation: " + RESOLUTION_MAP.get(team, "p4")

if __name__ == "__main__":
    result = fetch_nhl_game_result()
    print(result)