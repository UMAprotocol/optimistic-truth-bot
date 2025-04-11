import requests
from dotenv import load_dotenv
import os
import datetime

def fetch_game_result():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')
    
    # Define the teams and date from the question
    team1 = "Cavaliers"
    team2 = "Pacers"
    game_date = "2025-04-10"
    
    # Format the date for API call
    formatted_date = datetime.datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    
    # API endpoint setup
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{formatted_date}"
    headers = {
        'Ocp-Apim-Subscription-Key': api_key
    }
    
    try:
        # Make the API request
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()
        
        # Process the response to find the specific game
        for game in games:
            if (team1 in game['HomeTeam'] or team1 in game['AwayTeam']) and (team2 in game['HomeTeam'] or team2 in game['AwayTeam']):
                if game['Status'] == "Scheduled":
                    return "recommendation: p4"  # Game has not yet been played
                elif game['Status'] == "Postponed":
                    return "recommendation: p4"  # Game is postponed
                elif game['Status'] == "Canceled":
                    return "recommendation: p3"  # Game is canceled, resolve 50-50
                elif game['Status'] == "Final":
                    if game['HomeTeam'] == team1 and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: p2"  # Cavaliers win
                    elif game['AwayTeam'] == team1 and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: p2"  # Cavaliers win
                    else:
                        return "recommendation: p1"  # Pacers win
        return "recommendation: p4"  # No matching game found
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return "recommendation: p4"  # Unable to fetch data

# Run the function and print the result
result = fetch_game_result()
print(result)