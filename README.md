# Stock Market Tracker & Predictor 📈

A REST API backend that tracks real-time stock prices, predicts the next 7 days of closing prices using Machine Learning, and analyzes news sentiment to factor market mood into predictions.

## Tech Stack
- Python
- Flask
- yfinance (Yahoo Finance API)
- scikit-learn (Linear Regression)
- NewsAPI
- TextBlob (Sentiment Analysis)
- pandas & numpy

## How It Works
1. Fetches 6 months of real historical stock data via Yahoo Finance
2. Runs a Linear Regression model to predict the next 7 closing prices
3. Pulls recent news headlines and scores sentiment (positive/negative/neutral)
4. Adjusts price predictions based on news sentiment
5. Returns everything as clean JSON

## How to Run
1. Clone the repo
2. Create a virtual environment: `python3 -m venv venv`
3. Activate it: `source venv/bin/activate`
4. Install dependencies: `pip install flask yfinance pandas scikit-learn matplotlib python-dotenv newsapi-python textblob`
5. Add your API keys to a `.env` file:
```
NEWS_API_KEY=your_newsapi_key_here
```
6. Run: `python3 app.py`

## Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stock?ticker=AAPL` | Get stock data, 7-day prediction, and news sentiment |
| GET | `/stock/compare?ticker1=AAPL&ticker2=TSLA` | Compare two stocks side by side |
| GET | `/stock/tickers` | See all supported tickers with descriptions |

## Example Response
```json
{
  "ticker": "TSLA",
  "current_price": 396.73,
  "predicted_trend": "UP",
  "7_day_predictions": [431.02, 431.01, 431.0, 431.0, 430.99, 430.98, 430.97],
  "news_sentiment": "POSITIVE",
  "sentiment_score": 0.077,
  "recent_headlines": ["Tesla Rival BYD Applies For Permit..."],
  "description": "Tesla Inc. — electric vehicles and clean energy"
}
```
