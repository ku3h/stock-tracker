from flask import Flask, jsonify, request
from model import get_stock_summary
from dotenv import load_dotenv
import difflib
import os

# Load environment variables from the .env file
load_dotenv()

# Create the Flask app
app = Flask(__name__)

# Dictionary mapping ticker symbols to company info
# Each entry has: company name (for news search) and a description (for users who don't know stocks)
TICKER_INFO = {
    "AAPL":  {"company": "Apple",               "description": "Apple Inc. — makes iPhone, Mac, iPad, and AirPods"},
    "TSLA":  {"company": "Tesla",               "description": "Tesla Inc. — electric vehicles and clean energy"},
    "GOOGL": {"company": "Google",              "description": "Alphabet Inc. — parent company of Google and YouTube"},
    "AMZN":  {"company": "Amazon",              "description": "Amazon.com — e-commerce, AWS cloud, and Prime"},
    "MSFT":  {"company": "Microsoft",           "description": "Microsoft Corp. — Windows, Office, Xbox, and Azure cloud"},
    "META":  {"company": "Meta Facebook",       "description": "Meta Platforms — Facebook, Instagram, and WhatsApp"},
    "NVDA":  {"company": "Nvidia",              "description": "Nvidia Corp. — GPUs powering gaming and AI"},
    "NFLX":  {"company": "Netflix",             "description": "Netflix Inc. — video streaming platform"},
    "AMD":   {"company": "AMD semiconductor",   "description": "Advanced Micro Devices — CPUs and GPUs competing with Intel and Nvidia"},
    "UBER":  {"company": "Uber",                "description": "Uber Technologies — ride sharing and food delivery"},
    "BABA":  {"company": "Alibaba",             "description": "Alibaba Group — Chinese e-commerce and cloud giant"},
    "JPM":   {"company": "JPMorgan Chase",      "description": "JPMorgan Chase — largest US bank by assets"},
    "DIS":   {"company": "Disney",              "description": "Walt Disney Co. — entertainment, theme parks, and Disney+"},
    "PYPL":  {"company": "PayPal",              "description": "PayPal Holdings — online payments and Venmo"},
    "INTC":  {"company": "Intel",               "description": "Intel Corp. — semiconductor chips for computers and servers"},
    "COIN":  {"company": "Coinbase",            "description": "Coinbase Global — largest US cryptocurrency exchange"},
    "GME":   {"company": "GameStop",            "description": "GameStop Corp. — video game retailer, famous for 2021 short squeeze"},
    "BA":    {"company": "Boeing",              "description": "Boeing Co. — commercial airplanes and defense"},
    "NKE":   {"company": "Nike",               "description": "Nike Inc. — athletic footwear and apparel"},
    "SPOT":  {"company": "Spotify",             "description": "Spotify Technology — music and podcast streaming"},
    "RBLX":  {"company": "Roblox",              "description": "Roblox Corp. — online gaming platform for kids and teens"},
    "COST":  {"company": "Costco",              "description": "Costco Wholesale — membership-based warehouse retailer"},
    "CSCO":  {"company": "Cisco",               "description": "Cisco Systems — networking hardware and cybersecurity"},
    "SBUX":  {"company": "Starbucks",           "description": "Starbucks Corp. — world's largest coffeehouse chain"},
    "AMC":   {"company": "AMC Entertainment",  "description": "AMC Entertainment — movie theater chain, popular meme stock"},
    "T":     {"company": "AT&T",               "description": "AT&T Inc. — telecom giant offering wireless and internet services"},
    "PLTR":  {"company": "Palantir",            "description": "Palantir Technologies — big data analytics for governments and enterprises"},
    "F":     {"company": "Ford",               "description": "Ford Motor Co. — cars and trucks, investing heavily in EVs"},
    "JNJ":   {"company": "Johnson and Johnson", "description": "Johnson & Johnson — healthcare, pharmaceuticals, and medical devices"},
    "PFE":   {"company": "Pfizer",              "description": "Pfizer Inc. — pharmaceutical giant, known for COVID-19 vaccine"},
    "MRNA":  {"company": "Moderna",             "description": "Moderna Inc. — biotech company known for mRNA COVID-19 vaccine"},
    "MRK":   {"company": "Merck",               "description": "Merck & Co. — global pharmaceutical and vaccine company"},
    "CVX":   {"company": "Chevron",             "description": "Chevron Corp. — one of the world's largest oil and gas companies"},
    "V":     {"company": "Visa",                "description": "Visa Inc. — global payments network used by billions"},
    "VZ":    {"company": "Verizon",             "description": "Verizon Communications — major US telecom and wireless provider"},
    "WBA":   {"company": "Walgreens",           "description": "Walgreens Boots Alliance — pharmacy and health retail chain"},
    "WMT":   {"company": "Walmart",             "description": "Walmart Inc. — world's largest retailer"},
    "WFC":   {"company": "Wells Fargo",         "description": "Wells Fargo & Co. — one of the largest US banks"},
}


@app.route("/stock", methods=["GET"])
def get_stock():
    """
    Main endpoint to get stock data, predictions, and news sentiment.
    Usage: GET /stock?ticker=AAPL
    Returns current price, 7-day prediction, trend, news sentiment, and company description.
    """

    # Get the ticker from the URL query parameter e.g. ?ticker=AAPL
    ticker = request.args.get("ticker")

    # Make sure the user actually provided a ticker
    if not ticker:
        return jsonify({"error": "Please provide a ticker symbol e.g. ?ticker=AAPL"}), 400

    # Convert to uppercase so aapl and AAPL both work
    ticker = ticker.upper()

    # Look up company info — name for news search, description for the user
    ticker_data = TICKER_INFO.get(ticker)
    company_name = ticker_data["company"] if ticker_data else ticker
    description = ticker_data["description"] if ticker_data else f"{ticker} — no description available yet"

    # Fetch stock data, run prediction, and get news sentiment
    summary = get_stock_summary(ticker, company_name)

    # If summary is None, the ticker was invalid or had no data
    if summary is None:
        # Try to find similar tickers the user might have meant
        all_tickers = list(TICKER_INFO.keys())
        close_matches = difflib.get_close_matches(ticker, all_tickers, n=3, cutoff=0.5)

        if close_matches:
            # Build helpful suggestions with descriptions so user knows what each one is
            suggestions = {t: TICKER_INFO[t]["description"] for t in close_matches}
            return jsonify({
                "error": f"Could not find data for ticker: {ticker}",
                "did_you_mean": suggestions,
                "tip": f"Try one of these instead: {', '.join(close_matches)}"
            }), 404
        else:
            # No similar tickers found at all
            return jsonify({
                "error": f"Could not find data for ticker: {ticker}",
                "tip": "Check the ticker symbol and try again. Use /stock/tickers to see all supported tickers."
            }), 404

    # Add the company description to the simmary before returning
    summary["description"] = description

    # Return the full summary as JSON
    return jsonify(summary)

# Route for comparing two stocks
@app.route("/stock/compare", methods = ["GET"])
def compare_stocks():
    """
    Compare two stocks side by side.
    Usage: GET /stock/compare?ticker1=AAPL&ticker2=TSLA
    Returns predictions on sentiment for both stocks so you can compare them.
    """

    # Get the tickers from the URL query parameter e.g. ?ticker1=AAPL&ticker2=TSLA
    ticker1 = request.args.get("ticker1")
    ticker2 = request.args.get("ticker2")

    # Make sure both tickers were provided 
    if not ticker1 or not ticker2:
        return jsonify({"error": "Please provide two tickers e.g. ?ticker1=AAPL&ticker2=TSLA"}), 400

    # Convert to uppercase so aapl and AAPL both work
    ticker1 = ticker1.upper()
    ticker2 = ticker2.upper()
    
    # Get company names for both tickers
    comapany1 = TICKER_INFO.get(ticker1, {}.get("company", ticker1))
    comapany2 = TICKER_INFO.get(ticker2, {}.get("company", ticker2))

    # Fetch data for both stocks
    summary1 = get_stock_summary(ticker1, comapany1)
    summary2 = get_stock_summary(ticker2, comapany2)

    #
    if summary1 is None:
        return jsonify({"error": f"Could not find data for ticker: {ticker1}"}), 404
    if summary2 is None:
        return jsonify({"error": f"Could not find data for ticker: {ticker2}"}), 404

    # Add descriptions to both summaries
    summary1["description"] = TICKER_INFO.get(ticker1, {}).get("description", "")
    summary2["description"] = TICKER_INFO.get(ticker2, {}).get("description", "")

    # Return both side by side
    return jsonify({
        ticker1: summary1,
        ticker2: summary2
    })

@app.route("/stock/tickers", methods=["GET"])
def get_supported_tickers():
    """
    Returns all supported tickers with their plain English descriptions.
    Usage: GET /stock/tickers
    """

    tickers_with_descriptions = {
        ticker: info["description"]
        for ticker, info in TICKER_INFO.items()
    }

    return jsonify({
        "supported_tickers": tickers_with_descriptions,
        "tip": "You can also try any valid stock ticker which is not listed here!"
    })

# Start the Flask server in debug mode
if __name__ == "__main__":
    app.run(debug=True)