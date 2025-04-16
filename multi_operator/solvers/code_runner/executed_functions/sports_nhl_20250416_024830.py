import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    game_date = "2025-04-15"
    team_anaheim = "ANA"
    team_minnesota = "MIN"

    RESOLUTION_MAP = {
        "ANA": "p2",  # Anaheim Ducks
        "MIN": "p1",  # Minnesota Wild
        "50-50": "p3",
        "Too early to resolve": "p4",
    }

    if not api_key:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={api_key}"
    headers = {'Ocp-Apim-Subscription-Key': api_key}

    try:
        response = requests.get(url, headers=headers)
        games = response.json()

        for game in games:
            if game['HomeTeam'] == team_anaheim and game['AwayTeam'] == team_minnesota or \
               game['HomeTeam'] == team_minnesota and game['AwayTeam'] == team_anaheim:
                if game['Status'] == "Final":
                    home_team_score = game['HomeTeamScore']
                    away_team_score = game['AwayTeamScore']
                    if home_team_score > away_team_score:
                        winning_team = game['HomeTeam']
                    else:
                        winning_team = game['AwayTeam']
                    return "recommendation: " + RESOLUTION_MAP[winning_team]
                elif game['Status'] == "Postponed":
                    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Canceled":
                    return "recommendation: " + RESOLUTION_MAP["50-50"]
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    except Exception as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

print(fetch_nhl_game_result())