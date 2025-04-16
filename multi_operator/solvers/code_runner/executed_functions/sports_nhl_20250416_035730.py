import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    game_date = "2025-04-15"
    team_1 = "VGK"  # Vegas Golden Knights
    team_2 = "CGY"  # Calgary Flames

    RESOLUTION_MAP = {
        "VGK": "p2",  # Golden Knights win
        "CGY": "p1",  # Flames win
        "50-50": "p3",
        "Too early to resolve": "p4",
    }

    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={api_key}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] in [team_1, team_2] and game['AwayTeam'] in [team_1, team_2]:
                if game['Status'] == "Final":
                    if game['HomeTeam'] == team_1 and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_1]
                    elif game['AwayTeam'] == team_1 and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_1]
                    elif game['HomeTeam'] == team_2 and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_2]
                    elif game['AwayTeam'] == team_2 and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: " + RESOLUTION_MAP[team_2]
                elif game['Status'] == "Postponed":
                    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
                elif game['Status'] == "Canceled":
                    return "recommendation: " + RESOLUTION_MAP["50-50"]
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

print(fetch_nhl_game_result())