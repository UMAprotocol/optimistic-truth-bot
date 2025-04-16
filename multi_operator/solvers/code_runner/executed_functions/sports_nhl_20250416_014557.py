import requests
from dotenv import load_dotenv
import os

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    url = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-15"
    headers = {
        "Ocp-Apim-Subscription-Key": api_key
    }

    try:
        response = requests.get(url, headers=headers)
        games = response.json()
        for game in games:
            if game['HomeTeam'] == 'NJD' and game['AwayTeam'] == 'BOS':
                if game['Status'] == 'Final':
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return "recommendation: p2"  # Devils win
                    elif away_score > home_score:
                        return "recommendation: p1"  # Bruins win
                elif game['Status'] == 'Postponed':
                    return "recommendation: p4"  # Game postponed
                elif game['Status'] == 'Canceled':
                    return "recommendation: p3"  # Game canceled, no make-up
    except Exception as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: p4"  # Unable to resolve due to error

    return "recommendation: p4"  # Default case if no specific condition met

# Execute the function and print the result
result = fetch_nhl_game_result()
print(result)