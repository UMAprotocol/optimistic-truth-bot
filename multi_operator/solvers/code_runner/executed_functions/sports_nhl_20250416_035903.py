import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    if not api_key:
        return "recommendation: p4"  # API key not found, cannot proceed

    game_date = "2025-04-15"
    team_1 = "VGK"  # Vegas Golden Knights
    team_2 = "CGY"  # Calgary Flames

    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={api_key}"
    headers = {'Ocp-Apim-Subscription-Key': api_key}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == team_1 and game['AwayTeam'] == team_2 or game['HomeTeam'] == team_2 and game['AwayTeam'] == team_1:
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        winning_team = game['HomeTeam']
                    else:
                        winning_team = game['AwayTeam']

                    RESOLUTION_MAP = {
                        "VGK": "p2",  # Golden Knights
                        "CGY": "p1",  # Flames
                        "50-50": "p3",
                        "Too early to resolve": "p4",
                    }

                    return "recommendation: " + RESOLUTION_MAP.get(winning_team, "p4")
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"  # Game postponed, resolve later
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"  # Game canceled, resolve as 50-50
        return "recommendation: p4"  # No matching game found or game not yet played
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: p4"  # Error in fetching data

# Example usage
result = fetch_nhl_game_result()
print(result)