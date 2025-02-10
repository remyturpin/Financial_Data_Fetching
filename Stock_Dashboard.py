import os
import subprocess
import sys

# Automatically install missing dependencies
required_packages = ["streamlit", "pandas", "numpy", "yfinance", "plotly", "openai", "alpha_vantage", "stocknews"]

for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import openai
from datetime import datetime
from alpha_vantage.fundamentaldata import FundamentalData
from stocknews import StockNews

# Open AI Api Key
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
else:
    st.error("🚨 OpenAI API Key is missing! Please set it in Streamlit Secrets.")

st.title('Stock Dashboard')

# User input
ticker = st.sidebar.text_input('Ticker', value='AAPL')
start_date = st.sidebar.date_input('Start Date', pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input('End Date', pd.to_datetime("today"))

# Check before downloading data
if ticker:
    data = yf.download(ticker, start=start_date, end=end_date)

    if data.empty:
        st.error(f"No data found for ticker '{ticker}'. Check the symbol or date range.")
    else:
        # Display the price chart
        if "Close" in data.columns:
            fig = px.line(data, x=data.index, y=data["Close"].squeeze(), title=f"{ticker} - Close Price")
            st.plotly_chart(fig)
        else:
            st.warning("Price data is not available.")

        # Create tabs
        pricing_data, fundamental_data, news, openai_tab = st.tabs(["Pricing Data", "Fundamental Data", "Top 10 News", "OpenAI Analysis"])

        # **Price Analysis**
        with pricing_data:
            st.header('Price Movements')
            data['% Change'] = data['Close'].pct_change()
            data.dropna(inplace=True)
            st.write(data)
            annual_return = data['% Change'].mean() * 252 * 100
            st.write(f'Annual Return: {annual_return:.2f}%')
            stdev = np.std(data['% Change']) * np.sqrt(252)
            st.write(f'Standard Deviation: {stdev:.2f}%')
            st.write(f'Risk Adj. Return: {annual_return / (stdev * 100):.2f}')

        # **Fundamental Data with Alpha Vantage**
        with fundamental_data:
            key = "OW1639L63B5UCYYL"
            fd = FundamentalData(key, output_format='pandas')

            st.subheader('Balance Sheet')
            try:
                balance_sheet, _ = fd.get_balance_sheet_annual(ticker)
                st.write(balance_sheet)
            except Exception as e:
                st.error(f"Error loading balance sheet : {str(e)}")

            st.subheader('Income Statement')
            try:
                income_statement, _ = fd.get_income_statement_annual(ticker)
                st.write(income_statement)
            except Exception as e:
                st.error(f"Error loading Income Statement : {str(e)}")

            st.subheader('Cash Flow Statement')
            try:
                cash_flow, _ = fd.get_cash_flow_annual(ticker)
                st.write(cash_flow)
            except Exception as e:
                st.error(f"Error loading Cashflow Statement : {str(e)}")

        #  **Stock News**
        with news:
            st.header(f'News of {ticker}')
            try:
                sn = StockNews(ticker, save_news=False)
                df_news = sn.read_rss()
                for i in range(min(10, len(df_news))):
                    st.subheader(f'News {i+1}')
                    st.write(df_news['published'][i])
                    st.write(df_news['title'][i])
                    st.write(df_news['summary'][i])
                    st.write(f"Title Sentiment: {df_news['sentiment_title'][i]}")
                    st.write(f"News Sentiment: {df_news['sentiment_summary'][i]}")
            except Exception as e:
                st.error(f"Error loading news : {str(e)}")

    # **OpenAI Analysis**
    from openai import OpenAIError

    client = openai.OpenAI(api_key=API_KEY_OPENAI)

    def get_openai_response(prompt):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except OpenAIError as e:
            return f" OpenAI error : {str(e)}"
        except Exception as e:
            return f" Unexpected error : {str(e)}"

    # OpenAI Analysis
    with openai_tab:
        buy_reason, sell_reason, swot_analysis = st.tabs(["3 Reasons to Buy", "3 Reasons to Sell", "SWOT Analysis"])

        with buy_reason:
            st.subheader(f'3 Reasons to BUY {ticker} Stock')
            buy_analysis = get_openai_response(f"Give me 3 reasons to buy {ticker} stock.")
            st.write(buy_analysis)

        with sell_reason:
            st.subheader(f'3 Reasons to SELL {ticker} Stock')
            sell_analysis = get_openai_response(f"Give me 3 reasons to sell {ticker} stock.")
            st.write(sell_analysis)

        with swot_analysis:
            st.subheader(f'SWOT Analysis of {ticker} Stock')
            swot_text = get_openai_response(f"Provide a detailed SWOT (Strengths, Weaknesses, Opportunities, Threats) analysis for {ticker} stock.")
            st.write("DEBUG SWOT RESPONSE:", swot_text)

            if not swot_text:
                swot_text = "No response received from Open AI for SWOT Analysis"

            st.write(swot_text)

else:
    st.warning("Enter a ticker to display data")
