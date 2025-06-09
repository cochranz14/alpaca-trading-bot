import os
import logging
from flask import Flask, request, jsonify
import alpaca_trade_api as tradeapi
from dotenv import load_dotenv

# Load environment variables (useful if you're running locally or via Render secrets)
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Load Alpaca API keys from environment variables
API_KEY = 'PKCQ9T5S0TI27QL9D8VR'
API_SECRET = 'jpL9CQHyDnMZ44N5dDfYqkeOVGkK2NRGfxcKulo6'
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"  # Use live URL for real trading

# Connect to Alpaca
api = tradeapi.REST(ALPACA_API_KEY, ALPACA_API_SECRET, ALPACA_BASE_URL, api_version='v2')


@app.route('/')
def home():
    return "Alpaca Trading Bot is running."


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    logging.info(f"Received webhook data: {data}")

    if not data or 'ticker' not in data or 'action' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    symbol = data['ticker']
    action = data['action'].lower()

    try:
        account = api.get_account()
        buying_power = float(account.buying_power)
        max_trade_value = 0.10 * buying_power

        # Get the last price
        last_quote = api.get_last_quote(symbol)
        current_price = last_quote.askprice or last_quote.bidprice

        if not current_price or current_price == 0:
            return jsonify({'error': 'Invalid market price'}), 400

        quantity = int(max_trade_value // current_price)
        if quantity == 0:
            return jsonify({'error': 'Not enough buying power'}), 400

        if action == 'buy':
            api.submit_order(
                symbol=symbol,
                qty=quantity,
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            logging.info(f"BUY order placed: {symbol}, qty={quantity}")

        elif action == 'sell':
            api.submit_order(
                symbol=symbol,
                qty=quantity,
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            logging.info(f"SELL order placed: {symbol}, qty={quantity}")

        else:
            return jsonify({'error': 'Invalid action'}), 400

        return jsonify({'status': f'{action} order placed', 'symbol': symbol, 'quantity': quantity}), 200

    except Exception as e:
        logging.error(f"Error handling order: {e}")
        return jsonify({'error': str(e)}), 500
