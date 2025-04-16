import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    game_date = "2025-04-14"
    team1 = "NYR"  # New York Rangers
    team2 = "FLA"  # Florida Panthers

    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={api_key}"
    headers = {'Ocp-Apim-Subscription-Key': api_key}

    RESOLUTION_MAP = {
        "NYR": "p2",  # Rangers
        "FLA": "p1",  # Panthers
        "50-50": "p3",
        "Too early to resolve": "p4",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] in [team1, team2] and game['AwayTeam'] in [team1, team2]:
                if game['Status'] == "Final":
                    if game['HomeTeamScore'] > game['AwayTeamScore']:
                        winning_team = game['HomeTeam']
                    else:
                        winning_team = game['AwayTeam']
                    return "recommendation: " + RESOLUTION_MAP[winning_team]
                elif game['Status'] == "Postponed":
                    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Canceled":
                    return "recommendation: " + RESOLUTION_MAP["50-50"]
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Example usage
result = fetch_nhl_game_result()
print(result)