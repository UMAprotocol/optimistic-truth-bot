import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    game_date = "2025-04-14"
    team_sharks = "SJS"
    team_canucks = "VAN"

    RESOLUTION_MAP = {
        "SJS": "p2",  # San Jose Sharks
        "VAN": "p1",  # Vancouver Canucks
        "50-50": "p3",
        "Too early to resolve": "p4",
    }

    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == team_sharks and game['AwayTeam'] == team_canucks or \
               game['HomeTeam'] == team_canucks and game['AwayTeam'] == team_sharks:
                if game['Status'] == "Final":
                    if game['HomeTeam'] == team_sharks and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_sharks]
                    elif game['HomeTeam'] == team_canucks and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_canucks]
                    elif game['AwayTeam'] == team_sharks and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_sharks]
                    elif game['AwayTeam'] == team_canucks and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_canucks]
                elif game['Status'] == "Postponed":
                    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Canceled":
                    return "recommendation: " + RESOLUTION_MAP["50-50"]
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

print(fetch_nhl_game_result())