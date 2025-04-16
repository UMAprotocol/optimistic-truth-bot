import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    game_date = "2025-04-14"
    team_a = "NYR"  # New York Rangers
    team_b = "FLA"  # Florida Panthers

    RESOLUTION_MAP = {
        "NYR": "p2",  # Rangers win
        "FLA": "p1",  # Panthers win
        "50-50": "p3",
        "Too early to resolve": "p4",
    }

    if not api_key:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={api_key}"
    headers = {'Ocp-Apim-Subscription-Key': api_key}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] in [team_a, team_b] and game['AwayTeam'] in [team_a, team_b]:
                if game['Status'] == "Final":
                    if game['HomeTeam'] == team_a and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_a]
                    elif game['AwayTeam'] == team_a and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_a]
                    elif game['HomeTeam'] == team_b and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_b]
                    elif game['AwayTeam'] == team_b and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_b]
                elif game['Status'] == "Postponed":
                    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Canceled":
                    return "recommendation: " + RESOLUTION_MAP["50-50"]
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

print(fetch_nhl_game_result())