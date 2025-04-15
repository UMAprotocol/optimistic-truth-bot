import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    game_date = "2025-04-14"
    team_1 = "LAK"  # Los Angeles Kings
    team_2 = "EDM"  # Edmonton Oilers

    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={api_key}"
    headers = {'Ocp-Apim-Subscription-Key': api_key}

    try:
        response = requests.get(url, headers=headers)
        games = response.json()
        for game in games:
            if game['HomeTeam'] == team_1 and game['AwayTeam'] == team_2 or game['HomeTeam'] == team_2 and game['AwayTeam'] == team_1:
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score and game['HomeTeam'] == team_1:
                        return "recommendation: p2"  # Kings win
                    elif home_score > away_score and game['HomeTeam'] == team_2:
                        return "recommendation: p1"  # Oilers win
                    elif away_score > home_score and game['AwayTeam'] == team_1:
                        return "recommendation: p2"  # Kings win
                    elif away_score > home_score and game['AwayTeam'] == team_2:
                        return "recommendation: p1"  # Oilers win
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"  # Game postponed
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"  # Game canceled, resolve 50-50
        return "recommendation: p4"  # No game found or future game
    except Exception as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: p4"  # Error case

# Example usage
result = fetch_nhl_game_result()
print(result)