import requests
from datetime import datetime, timedelta
import pytz

def fetch_binance_price(date, symbol="BTCUSDT"):
    """Fetch the closing price of a cryptocurrency from Binance at a specific date and time."""
    # Convert the date to the correct format and timezone for Binance API (UTC)
    utc_date = date.astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')
    base_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": "1m",
        "startTime": int(date.timestamp() * 1000),  # Convert to milliseconds
        "endTime": int((date + timedelta(minutes=1)).timestamp() * 1000)  # One minute later
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        # Extract the close price from the first (and only) candle returned
        close_price = float(data[0][4])  # Closing price is the fifth element in the list
        return close_price
    except requests.RequestException as e:
        print(f"Error fetching data from Binance: {e}")
        return None

def resolve_market():
    # Define the dates and times for price comparison in Eastern Time
    et_timezone = pytz.timezone('America/New_York')
    date1 = datetime(2025, 4, 9, 12, 0, tzinfo=et_timezone)
    date2 = datetime(2025, 4, 10, 12, 0, tzinfo=et_timezone)

    # Fetch prices
    price1 = fetch_binance_price(date1)
    price2 = fetch_binance_price(date2)

    if price1 is None or price2 is None:
        print("Failed to fetch one or both prices.")
        return "recommendation: p3"  # Unknown or error case

    # Compare prices and resolve the market
    if price1 < price2:
        return "recommendation: p2"  # Up
    elif price1 > price2:
        return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # 50-50

# Run the resolution function and print the result
result = resolve_market()
print(result)