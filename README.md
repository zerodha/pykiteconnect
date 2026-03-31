from kiteconnect import KiteConnect
import pandas as pd
import time

# Kite API Authentication
api_key = "YOUR_API_KEY"
api_secret = "YOUR_API_SECRET"
access_token = "YOUR_ACCESS_TOKEN"

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

# Fetch historical data
def get_data(symbol, interval="5minute"):
    data = kite.historical_data(
        instrument_token=kite.ltp(symbol)['instrument_token'],
        from_date=pd.Timestamp.now() - pd.Timedelta(days=1),
        to_date=pd.Timestamp.now(),
        interval=interval
    )
    return pd.DataFrame(data)

# VWAP Calculation
def calculate_vwap(df):
    df['VWAP'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()
    return df

# RSI Calculation
def calculate_rsi(df, window=14):
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=window).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# Strategy: Buy/Sell signal based on VWAP & RSI
def trade_logic(df):
    if df['close'].iloc[-1] > df['VWAP'].iloc[-1] and df['RSI'].iloc[-1] > 50:
        print("Buy Signal Generated!")
        # Example: place buy order (replace with real order)
        # kite.place_order(...)

    elif df['RSI'].iloc[-1] > 70:
        print("Sell Signal Generated!")
        # Example: place sell order (replace with real order)
        # kite.place_order(...)

# Main loop
symbol = "NSE:INFY"  # Replace with the stock symbol you want to trade

while True:
    data = get_data(symbol)
    data = calculate_vwap(data)
    data = calculate_rsi(data)
    
    # Execute trade logic
    trade_logic(data)
    
    # Wait for 5 minutes before next data fetch
    time.sleep(300)  # 5 minutes (300 seconds)
