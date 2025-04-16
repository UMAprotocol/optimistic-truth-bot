import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    if not api_key:
        return "recommendation: p4"  # API key not found, cannot proceed

    game_date = "2025-04-15"
    team_anaheim = "ANA"
    team_minnesota = "MIN"

    RESOLUTION_MAP = {
        team_anaheim: "p2",  # Ducks
        team_minnesota: "p1",  # Wild
        "50-50": "p3",
        "Too early to resolve": "p4",
    }

    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] in [team_anaheim, team_minnesota] or game['AwayTeam'] in [team_anaheim, team_minnesota]:
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
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: p4"  # Error in fetching data

    return "recommendation: p4"  # No relevant game found or game not yet played

# Example usage
result = fetch_nhl_game_result()
print(result)