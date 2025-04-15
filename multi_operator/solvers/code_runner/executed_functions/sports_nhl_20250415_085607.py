from dotenv import load_dotenv
import os
import requests

def fetch_nhl_game_result():
    load_dotenv()
    api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
    if not api_key:
        return "recommendation: p4"  # Unable to resolve due to missing API key

    url = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-14"
    headers = {
        "Ocp-Apim-Subscription-Key": api_key
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return "recommendation: p4"  # Unable to resolve due to API error

    # Define resolution map with team abbreviations
    RESOLUTION_MAP = {
        "LAK": "p2",  # Los Angeles Kings
        "EDM": "p1",  # Edmonton Oilers
        "50-50": "p3",
        "Too early to resolve": "p4",
    }

    # Search for the specific game
    for game in games:
        if game['HomeTeam'] == "LAK" and game['AwayTeam'] == "EDM":
            if game['Status'] == "Final":
                if game['HomeTeamScore'] > game['AwayTeamScore']:
                    return "recommendation: " + RESOLUTION_MAP["LAK"]
                elif game['AwayTeamScore'] > game['HomeTeamScore']:
                    return "recommendation: " + RESOLUTION_MAP["EDM"]
            elif game['Status'] == "Postponed":
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
            elif game['Status'] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            break

    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Execute the function and print the result
result = fetch_nhl_game_result()
print(result)