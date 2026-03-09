import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from newsapi import NewsApiClient
from textblob import TextBlob
import os
from dotenv import load_dotenv

# Load our API KEYS from the .env file
load_dotenv()

# Initialize the NewsAPI client with our API key
newsapi = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))

def get_stock_data(ticker):
    """
    Fetch the last 6 months of historical stock data
    for a given ticker symbol (e.g. AAPL, TSLA, GOOG, etc)
    """
    stock = yf.Ticker(ticker)
    df = stock.history(period = "6mo")

    # If no data came back, the ticker is most likely invalid
    if df.empty:
        return None

    # Round the closing prices to 2 decimal places
    df["Close"] = df["Close"].round(2)

    return df

def get_news_sentiment(company_name):
    """
    Fetch the last 30 days of news headlines for a comapany 
    and analyze whether the overall sentiment is positive or negative.
    TextBlob scores each headline from -1.0 (very negative) to +1.0 (very positive)
    """
    try :
        # Fetch top 10 recent headlines about the company
        articles = newsapi.get_everything(
            q = company_name,
            language = "en",
            sort_by = "publishedAt",
            page_size = 10
        )

        headlines = []
        sentiment_scores = []

        # Extract the headline text from each article
        for article in articles["articles"]:
            title = article["title"]
            if title:
                headlines.append(title)
                # Use TextBlob to analyze the sentiment of each headline
                # .sentiment.polarity gives a score from -1.0 to +1.0
                score = TextBlob(title).sentiment.polarity
                sentiment_scores.append(score)

        # Calculate the average sentiment score all the headlines
        if sentiment_scores:
            avg_sentiment = round(sum(sentiment_scores) / len(sentiment_scores), 3)
        else:
            avg_sentiment = 0.0

        # Label the sentiment as POSITIVE, NEGATIVE, or NEUTRAL
        if avg_sentiment > 0.05:
            sentiment_label = "POSITIVE"
        elif avg_sentiment < -0.05:
            sentiment_label = "NEGATIVE"
        else:
            sentiment_label = "NEUTRAL"

        return {
            "sentiment_label": sentiment_label,
            "sentiment_score": avg_sentiment,
            "recent_headlines": headlines[:5] # Return top 5 headlines
        }
    
    except Exception as e:
        # If news fect fails, return neutral so the app doesn't crash
        print(f"News fetch error: {e}")
        return {
            "sentiment_label": "NEUTRAL",
            "sentiment_score": 0.0,
            "recent_headlines": []
        }


def predict_price(df, sentiment_score = 0.0):
    """
    Use Linear Regression to predict the next 7 days of closing prices.
    Linear Regression draws a best-fit line through historical prices
    and extends it into the future.
    """

    # Create a numeric index for each day (0, 1, 2, 3,...)
    # Machine learning models require numeric data not dates
    df = df.copy()
    df["Day"] = np.arange(len(df))

    # X = the day numbers (input), y = the closing prices (output)
    X = df[["Day"]]
    y = df["Close"]

    # Train the linear regression model on historical data
    model = LinearRegression()
    model.fit(X, y)

    # Predict the next 7 days of closing prices beyond the last day in the dataset
    last_day = df["Day"].max()
    future_days = np.arange(last_day + 1, last_day + 8).reshape(-1, 1)
    predicted_prices = model.predict(future_days)

    # Apply a small sentiment adjustment to the predicted prices
    # For example: sentiment_score of 0.3 adds 0.3% to each predicted price
    # Round the predicted prices to 2 decimal places

    sentiment_multiplier = 1 + (sentiment_score * 0.003)
    predicted_prices = [round(p * sentiment_multiplier, 2) for p in predicted_prices]

    return predicted_prices
    

def get_stock_summary(ticker, company_name):
    """
    Main fuction which that combines fetching data and predicting prices.
    Returns a clean dicitonary ready to be send as JSON.
    """

    # Step 1: Get Historical Data
    df = get_stock_data(ticker)

    if df is None:
        return None

    # Step 2: Get news sentiment for the company
    news_data = get_news_sentiment(company_name)

    # Step 3: Predict future prices using both price history and sentiment
    predictions = predict_price(df, news_data["sentiment_score"])

    # Step 4: Build the full summary response
    summary = {
        "ticker": ticker.upper(),
        "current_price": float(df["Close"].iloc[-1]),
        "open_price": float(df["Open"].iloc[-1].round(2)),
        "high_price": float(df["High"].iloc[-1].round(2)),
        "low_price": float(df["Low"].iloc[-1].round(2)),
        "7_day_predictions": predictions,

        # Trend is Up if the last predicted price is higher than today's closing price
        "predicted_trend": "UP" if predictions[-1] > float(df["Close"].iloc[-1]) else "DOWN",

        # News sentiment date
        "news_sentiment": news_data["sentiment_label"],
        "sentiment_score": news_data["sentiment_score"],
        "recent_headlines": news_data["recent_headlines"],

        # Last 30 days of closing prices for charting
        "historical_closes": df["Close"].tolist()[-30:] # Last 30 days of closing prices
    }

    return summary