from dotenv import load_dotenv
import os
import requests

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
            if game['HomeTeam'] == 'DET' and game['AwayTeam'] == 'DAL':
                if game['Status'] == 'Final':
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return "DET"  # Red Wings win
                    elif away_score > home_score:
                        return "DAL"  # Stars win
                elif game['Status'] == 'Postponed':
                    return "Postponed"
                elif game['Status'] == 'Canceled':
                    return "Canceled"
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "Error"

    return "Too early to resolve"

def resolve_market():
    RESOLUTION_MAP = {
        "DAL": "p2",  # Dallas Stars
        "DET": "p1",  # Detroit Red Wings
        "Postponed": "p4",  # Market remains open
        "Canceled": "p3",  # Market resolves 50-50
        "Too early to resolve": "p4",
        "Error": "p4"
    }

    result = fetch_nhl_game_result()
    return "recommendation: " + RESOLUTION_MAP[result]

print(resolve_market())