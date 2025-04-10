import requests
from datetime import datetime, timedelta
import pytz

def fetch_binance_price(date, symbol="BTCUSDT"):
    """Fetch the closing price of a cryptocurrency from Binance at a specific date and time."""
    base_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 1,
        "startTime": int(date.timestamp() * 1000),  # Convert to milliseconds
        "endTime": int(date.timestamp() * 1000)
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            return float(data[0][4])  # Closing price is the fifth element in the list
        else:
            return None
    except requests.RequestException as e:
        print(f"Error fetching data from Binance: {e}")
        return None

def resolve_market():
    # Define the timezone
    et_timezone = pytz.timezone('America/New_York')
    
    # Define the dates for price comparison
    date1 = datetime(2025, 4, 9, 12, 0, tzinfo=et_timezone)
    date2 = datetime(2025, 4, 10, 12, 0, tzinfo=et_timezone)
    
    # Fetch prices
    price1 = fetch_binance_price(date1)
    price2 = fetch_binance_price(date2)
    
    # Check and compare prices
    if price1 is None or price2 is None:
        print("Failed to fetch prices.")
        return "recommendation: p4"
    elif price1 < price2:
        return "recommendation: p2"  # Up
    elif price1 > price2:
        return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # 50-50

# Execute the resolution function and print the result
result = resolve_market()
print(result)