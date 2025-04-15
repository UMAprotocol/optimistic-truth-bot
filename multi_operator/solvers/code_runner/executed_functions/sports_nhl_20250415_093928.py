import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    game_date = "2025-04-14"
    team1 = "SJS"  # San Jose Sharks
    team2 = "VAN"  # Vancouver Canucks

    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={api_key}"
    headers = {'Ocp-Apim-Subscription-Key': api_key}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == team1 and game['AwayTeam'] == team2 or game['HomeTeam'] == team2 and game['AwayTeam'] == team1:
                if game['Status'] == "Final":
                    home_team_win = game['HomeTeamScore'] > game['AwayTeamScore']
                    if (home_team_win and game['HomeTeam'] == team1) or (not home_team_win and game['AwayTeam'] == team1):
                        return resolve_recommendation(team1)
                    else:
                        return resolve_recommendation(team2)
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"  # Market remains open
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"  # Resolve 50-50
        return "recommendation: p4"  # No game found or too early to resolve
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return "recommendation: p4"  # Unable to resolve due to API error

def resolve_recommendation(team):
    RESOLUTION_MAP = {
        "SJS": "p2",  # Sharks
        "VAN": "p1",  # Canucks
        "50-50": "p3",
        "Too early to resolve": "p4",
    }
    return "recommendation: " + RESOLUTION_MAP.get(team, "p4")

if __name__ == "__main__":
    result = fetch_nhl_game_result()
    print(result)