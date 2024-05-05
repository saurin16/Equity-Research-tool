import streamlit as st
import openai
import yfinance as yf
import re
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates

openai.api_key = "YOUR_API_KEY_HERE"
client = openai.OpenAI(api_key="YOUR API KEY HERE")

# Define functions to fetch stock data, calculate financial indicators, and plot stock prices

st.markdown(
    '''
    <style>
    body {
        background-color: #000000;
        color: #ffffff;  /* Set text color to white */
    }
    </style>
    ''',
    unsafe_allow_html=True
)
@st.cache_data
def get_stock_price(ticker):
    return str(yf.Ticker(ticker).history(period='1y').iloc[-1].Close)

@st.cache_data
def calculate_SMA(ticker, window):
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.rolling(window=window).mean().iloc[-1])

@st.cache_data
def calculate_EMA(ticker, window):
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.ewm(span=window, adjust=False).mean().iloc[-1])

@st.cache_data
def calculate_RSI(ticker):
    data = yf.Ticker(ticker).history(period='1y').Close
    delta = data.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=14-1, adjust=False).mean()
    ema_down = down.ewm(com=14-1, adjust=False).mean()
    rs = ema_up / ema_down
    if not data.empty:
        return  str(100 - (100 / (1 + rs)).iloc[-1])
    else:
        return "No data available"
   

@st.cache_data
def calculate_MACD(ticker):
    data = yf.Ticker(ticker).history(period='1y').Close
    short_EMA = data.ewm(span=12, adjust=False).mean()
    long_EMA = data.ewm(span=26, adjust=False).mean()
    MACD = (short_EMA - long_EMA)
    signal = MACD.ewm(span=9, adjust=False).mean()
    MACD_histogram = MACD - signal
    if not data.empty:
        return  f'{MACD[-1]},{signal[-1]},{MACD_histogram[-1]}'

    else:
        return "No data available"
   

@st.cache_data
def plot_stock_price(ticker):
    data = yf.Ticker(ticker).history(period='1y')
    print(f"Ticker: {ticker}")
    print(data) 

    if data.empty:
        st.write(f"No data available for {ticker} over the last year.")
        return None
    data.index = pd.to_datetime(data.index)

    # Create a figure and axis object
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot the data as a line graph
    ax.plot(data.index, data['Close'])

    # Set the title, x-label, and y-label
    ax.set_title(f'{ticker} Stock Price Over Last Year', fontsize=16)
    ax.set_xlabel('Date', fontsize=14)
    ax.set_ylabel('Stock Price ($)', fontsize=14)

    # Rotate x-axis labels for better visibility
    plt.xticks(rotation=45, ha='right')

    # Set the x-axis tick format to display dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    st.set_option('deprecation.showPyplotGlobalUse', False)
    return fig

# Define chatbot logic using Streamlit
st.title("Financial Stock Assistant Chatbot")

user_input = st.text_input("Enter your query:")

if user_input:
    try:
        # Generate response from OpenAI based on user input
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=user_input,
            max_tokens=100,
            temperature=0.7,
            stream=False # Add this line to explicitly specify non-streaming
        )
        
        # Parse response and execute corresponding functions
        response_text = response.choices[0].text
        if 'plot' in response_text and 'stock' in response_text and 'price' in response_text:
    # Extract ticker symbol using regex
             ticker_match = re.search(r'\b[A-Z]+\b', response_text)
             if ticker_match:
                   ticker = ticker_match.group()
                   fig = plot_stock_price(ticker)
                   st.pyplot(fig)
                   plt.close(fig)
             else:
                   st.write("Ticker symbol not found.")
        elif 'SMA' in response_text:
    # Extract ticker symbol and window size using regex
            matches = re.findall(r'\b[A-Z]+\b|\b\d+\b', response_text)
            if len(matches) >= 2:
              ticker = matches[1]
              window = int(matches[-1])
              result = calculate_SMA(ticker, window)
              st.write(f"The SMA of {ticker} with window {window} is: {result}")
            else:
              st.write("Ticker symbol or window size not found.")
        elif 'EMA' in response_text:
    # Extract ticker symbol and window size using regex
             matches = re.findall(r'\b[A-Z]+\b|\b\d+\b', response_text)
             if len(matches) >= 2:
               ticker = matches[0]  # Ticker symbol should be at index 0
               window = int(matches[-1])  # Window size should be at the last index
               result = calculate_EMA(ticker, window)
               st.write(f"The EMA of {ticker} with window {window} is: {result}")
             else:
               st.write("Ticker symbol or window size not found.")
        elif 'RSI' in response_text:
            # Extract ticker symbol using regex
            ticker_match = re.search(r'\b[A-Z]+\b', response_text)
            if ticker_match:
                ticker = ticker_match.group()
                result = calculate_RSI(ticker)
                st.write(f"The RSI of {ticker} is: {result}")
            else:
                st.write("Ticker symbol not found.")
        elif 'MACD' in response_text:
            # Extract ticker symbol using regex
            ticker_match = re.search(r'\b[A-Z]+\b', response_text)
            if ticker_match:
                ticker = ticker_match.group()
                result = calculate_MACD(ticker)
                st.write(f"The MACD of {ticker} is: {result}")
            else:
                st.write("Ticker symbol not found.")
        elif 'price' in response_text and 'stock' in response_text:
            # Extract ticker symbol using regex
            ticker_match = re.search(r'\b[A-Z]+\b', response_text)
            if ticker_match:
                ticker = ticker_match.group()
                result = get_stock_price(ticker)
                st.write(f"The stock price of {ticker} is: ${result}")
            else:
                st.write("Ticker symbol not found.")
        
        else:
            st.write("Sorry, I couldn't understand that.")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
