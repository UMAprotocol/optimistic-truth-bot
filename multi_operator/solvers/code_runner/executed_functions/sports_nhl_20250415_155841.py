import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    if not api_key:
        return "recommendation: p4"  # API key not found, cannot resolve

    url = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-14"
    headers = {
        "Ocp-Apim-Subscription-Key": api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['AwayTeam'] == "CHI" and game['HomeTeam'] == "MTL":
                if game['Status'] == "Final":
                    if game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: p2"  # Blackhawks win
                    elif game['AwayTeamScore'] < game['HomeTeamScore']:
                        return "recommendation: p1"  # Canadiens win
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"  # Game postponed, resolve later
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"  # Game canceled, resolve 50-50
    except requests.RequestException as e:
        print(f"Error fetching NHL data: {e}")
        return "recommendation: p4"  # Error occurred, cannot resolve

    return "recommendation: p4"  # No relevant game found or game not yet played

# Example usage
result = fetch_nhl_game_result()
print(result)