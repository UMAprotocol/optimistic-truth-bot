import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, start_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
    
    Args:
        symbol (str): The symbol to fetch data for.
        start_time (int): The start time in milliseconds for the data.
    
    Returns:
        float: The closing price of the symbol at the specified time.
    """
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 1,
        "startTime": start_time,
        "endTime": start_time + 3600000  # 1 hour later
    }
    
    try:
        # Try fetching from the proxy endpoint first
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Closing price
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary API.")
        # Fallback to the primary API endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            return float(data[0][4])  # Closing price
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

def resolve_market(symbol, target_date_str):
    """
    Resolves the market based on the price change of a cryptocurrency.
    
    Args:
        symbol (str): The cryptocurrency symbol.
        target_date_str (str): The target date in 'YYYY-MM-DD HH:MM' format.
    
    Returns:
        str: Market resolution recommendation.
    """
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d %H:%M")
    start_time = int(target_date.timestamp() * 1000)  # Convert to milliseconds
    
    closing_price = fetch_price_data(symbol, start_time)
    
    if closing_price is None:
        return "recommendation: p3"  # Unknown or API failure
    
    # Assuming the previous price check was done an hour earlier
    previous_price = fetch_price_data(symbol, start_time - 3600000)
    
    if previous_price is None or closing_price is None:
        return "recommendation: p3"  # Unknown or API failure
    
    if closing_price >= previous_price:
        return "recommendation: p2"  # Market resolves to "Up"
    else:
        return "recommendation: p1"  # Market resolves to "Down"

# Example usage
if __name__ == "__main__":
    # Example: Resolve for BTC/USDT on June 13, 2025, at 9 PM ET
    print(resolve_market("BTCUSDT", "2025-06-13 21:00"))