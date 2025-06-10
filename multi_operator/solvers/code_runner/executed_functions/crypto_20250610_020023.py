import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# Constants
DEXSCREENER_API_URL = "https://api.dexscreener.io/latest/dex/pairs/solana/gj5t6kjtw3gww7srmhei1ojckayhyvlwb17gktf96hnh"
START_DATE = "2025-05-07 15:00:00"
END_DATE = "2025-05-31 23:59:00"
TARGET_PRICE = 0.02500
TIMEZONE = "US/Eastern"

def fetch_data():
    """
    Fetches the historical price data for HOUSE/SOL from Dexscreener API.
    """
    # Convert dates to UTC timestamps
    start_dt = datetime.strptime(START_DATE, "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.strptime(END_DATE, "%Y-%m-%d %H:%M:%S")
    tz = pytz.timezone(TIMEZONE)
    start_dt = tz.localize(start_dt).astimezone(pytz.utc)
    end_dt = tz.localize(end_dt).astimezone(pytz.utc)

    # Prepare parameters for API request
    params = {
        "from": int(start_dt.timestamp()),
        "to": int(end_dt.timestamp())
    }

    try:
        response = requests.get(DEXSCREENER_API_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch data: {str(e)}")
        return None

def analyze_data(data):
    """
    Analyzes the fetched data to determine if the price of HOUSE/SOL dipped to or below the target price.
    """
    if not data or "pair" not in data or "chartData" not in data["pair"]:
        print("Invalid data format or data missing.")
        return "p4"

    for candle in data["pair"]["chartData"]:
        if float(candle["l"]) <= TARGET_PRICE:
            return "p2"  # Yes, it dipped to or below the target price

    return "p1"  # No, it did not dip to or below the target price

def main():
    """
    Main function to execute the process.
    """
    data = fetch_data()
    result = analyze_data(data)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()