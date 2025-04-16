import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    url = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-14"
    headers = {
        "Ocp-Apim-Subscription-Key": api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == "CHI" and game['AwayTeam'] == "MTL":
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return "recommendation: p2"  # Blackhawks win
                    elif away_score > home_score:
                        return "recommendation: p1"  # Canadiens win
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"  # Game postponed
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"  # Game canceled, resolve 50-50
    except requests.RequestException as e:
        print(f"Error fetching NHL data: {e}")
        return "recommendation: p4"  # Unable to resolve due to error

    return "recommendation: p4"  # Default case if no specific conditions met

# Example usage
result = fetch_nhl_game_result()
print(result)