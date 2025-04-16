import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    game_date = "2025-04-15"
    team_bruins = "BOS"
    team_devils = "NJD"

    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={api_key}"
    headers = {'Ocp-Apim-Subscription-Key': api_key}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == team_bruins or game['AwayTeam'] == team_bruins:
                if game['HomeTeam'] == team_devils or game['AwayTeam'] == team_devils:
                    if game['Status'] == "Final":
                        home_score = game['HomeTeamScore']
                        away_score = game['AwayTeamScore']
                        if (game['HomeTeam'] == team_bruins and home_score > away_score) or (game['AwayTeam'] == team_bruins and away_score > home_score):
                            return resolve_recommendation("BOS")
                        elif (game['HomeTeam'] == team_devils and home_score > away_score) or (game['AwayTeam'] == team_devils and away_score > home_score):
                            return resolve_recommendation("NJD")
                    elif game['Status'] == "Postponed":
                        return resolve_recommendation("Too early to resolve")
                    elif game['Status'] == "Canceled":
                        return resolve_recommendation("50-50")
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return resolve_recommendation("Too early to resolve")

    return resolve_recommendation("Too early to resolve")

def resolve_recommendation(team):
    RESOLUTION_MAP = {
        "BOS": "p1",
        "NJD": "p2",
        "50-50": "p3",
        "Too early to resolve": "p4",
    }
    return f"recommendation: {RESOLUTION_MAP[team]}"

if __name__ == "__main__":
    result = fetch_nhl_game_result()
    print(result)