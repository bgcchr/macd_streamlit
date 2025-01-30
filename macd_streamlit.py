import pandas as pd
import yfinance as yf
import time
import datetime
import streamlit as st
import matplotlib.pyplot as plt
import pytz

# Streamlit app title
st.title("📈 Live MACD Trading Bot")

# User input: Allow multiple stocks
watch_stocks = st.text_input("Enter stock symbols separated by commas (e.g., HDFCBANK.NS, RELIANCE.NS)", "HDFCBANK.NS")
watch_stocks = [stock.strip() for stock in watch_stocks.split(",")]

# Function to fetch stock data
def fetch_stock_data(ticker, period="1d", interval="1m"):
    df = yf.download(ticker, interval=interval, period=period)
    df.dropna(inplace=True)
    return df

# Function to calculate MACD
def calculate_macd(df, short_ema=30, long_ema=60, signal_ema=9):
    df['MACD_Line'] = df['Close'].ewm(span=short_ema, adjust=False).mean() - df['Close'].ewm(span=long_ema, adjust=False).mean()
    df['Signal_Line'] = df['MACD_Line'].ewm(span=signal_ema, adjust=False).mean()
    return df

# Convert UTC to Indian Standard Time (IST)
def convert_to_ist(df):
    ist = pytz.timezone('Asia/Kolkata')
    
    # Check if the index is timezone-aware
    if df.index.tzinfo is None:
        df.index = df.index.tz_localize('UTC')  # Localize to UTC if not already aware
    df.index = df.index.tz_convert(ist)  # Convert to IST
    
    return df

# Live MACD trading function
def check_macd_signal(stock):
    df = fetch_stock_data(stock)

    if df.empty or len(df) < 2:
        return None, None, None, None, None, None  # Not enough data

    df = convert_to_ist(df)  # Convert UTC time to IST
    df = calculate_macd(df)
    latest_macd = df['MACD_Line'].iloc[-1]
    latest_signal = df['Signal_Line'].iloc[-1]
    prev_macd = df['MACD_Line'].iloc[-2]
    prev_signal = df['Signal_Line'].iloc[-2]
    timestamp = df.index[-1]  # Get the latest timestamp
    difference = round(abs(latest_macd - latest_signal), 2)

    signal = "⚖️ No Signal"
    if prev_macd < prev_signal and latest_macd > latest_signal:
        signal = "🚀 BUY"
    elif prev_macd > prev_signal and latest_macd < latest_signal:
        signal = "🔻 SELL"

    return df, latest_macd, latest_signal, difference, signal, timestamp

# Live update in Streamlit
st.subheader("📡 Live Stock Updates (Auto-refreshes every minute)")
placeholder = st.empty()

while True:
    with placeholder.container():
        for stock in watch_stocks:
            df, latest_macd, latest_signal, difference, signal, timestamp = check_macd_signal(stock)

            if df is None:
                st.error(f"⚠️ Not enough data for {stock}")
                continue

            # Display stock details
            st.write(f"### {stock} - {timestamp}")
            st.write(f"**{signal}** | MACD: `{latest_macd:.2f}` | Signal: `{latest_signal:.2f}` | Diff: `{difference}`")

            # Plot MACD Chart
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df.index[-50:], df['MACD_Line'].iloc[-50:], label="MACD Line", color='blue')
            ax.plot(df.index[-50:], df['Signal_Line'].iloc[-50:], label="Signal Line", color='red')
            ax.axhline(0, color='black', linestyle='--', linewidth=0.5)
            ax.legend()
            ax.set_title(f"MACD Chart for {stock}")
            ax.set_xlabel("Time (IST)")
            ax.set_ylabel("MACD Value")
            ax.tick_params(axis='x', rotation=45)
            ax.grid()
            st.pyplot(fig)

    # Auto-refresh every 60 seconds
    time.sleep(60)
