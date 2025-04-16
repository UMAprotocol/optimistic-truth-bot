from dotenv import load_dotenv
import os
import requests

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    if not api_key:
        return "recommendation: p4"  # Unable to resolve due to missing API key

    url = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-15"
    headers = {
        "Ocp-Apim-Subscription-Key": api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == "NJD" and game['AwayTeam'] == "BOS":
                if game['Status'] == "Final":
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return "recommendation: p2"  # Devils win
                    elif away_score > home_score:
                        return "recommendation: p1"  # Bruins win
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"  # Game postponed, too early to resolve
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"  # Game canceled, resolve 50-50
        return "recommendation: p4"  # No matching game found or game not yet completed

    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: p4"  # Unable to resolve due to API error

# Example usage
result = fetch_nhl_game_result()
print(result)