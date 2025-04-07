import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def fetch_btc_price_history(start_date, end_date):
    """
    Fetches the historical high and low prices for BTCUSDT on Binance between two dates.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        A list of tuples containing (timestamp, high, low) for each day
    """
    symbol = "BTCUSDT"
    interval = "1d"  # daily intervals
    limit = 1000  # maximum number of data points

    start_time = int(datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=pytz.UTC).timestamp() * 1000)
    end_time = int(datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=pytz.UTC).timestamp() * 1000)

    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": limit
    }

    response = requests.get(url, params=params)
    response.raise_for_status()  # Will raise an exception for HTTP errors
    data = response.json()

    prices = []
    for entry in data:
        timestamp = entry[0]
        high = float(entry[2])
        low = float(entry[3])
        prices.append((timestamp, high, low))

    return prices

def analyze_prices(prices):
    """
    Analyzes the list of prices to determine if $80k or $90k was hit first.

    Args:
        prices: List of tuples (timestamp, high, low)

    Returns:
        Recommendation based on the analysis
    """
    first_80k = None
    first_90k = None

    for timestamp, high, low in prices:
        if low <= 80000.00 and first_80k is None:
            first_80k = timestamp
        if high >= 90000.00 and first_90k is None:
            first_90k = timestamp

        if first_80k and first_90k:
            break

    if first_80k and first_90k:
        if first_80k < first_90k:
            return "recommendation: p2"  # $80k hit first
        else:
            return "recommendation: p1"  # $90k hit first
    elif first_80k:
        return "recommendation: p2"
    elif first_90k:
        return "recommendation: p1"
    else:
        return "recommendation: p3"  # Neither price was hit

def main():
    start_date = "2025-03-28"
    end_date = "2025-12-31"
    prices = fetch_btc_price_history(start_date, end_date)
    recommendation = analyze_prices(prices)
    print(recommendation)

if __name__ == "__main__":
    main()