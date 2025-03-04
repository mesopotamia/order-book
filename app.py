import requests
import numpy as np
from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__)

# Binance API fetch function
def fetch_binance_data(endpoint, params, is_futures=False):
    base_url = "https://binance.com" if not is_futures else "https://fapi.binance.com"
    url = f"{base_url}{endpoint}"
    print(url)
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()

# Fetch trades data (spot or futures)
def get_trades(symbol="BTCUSDT", limit=1000, is_futures=False):
    endpoint = "/api/v3/trades" if not is_futures else "/fapi/v1/trades"
    params = {"symbol": symbol, "limit": limit}
    trades = fetch_binance_data(endpoint, params, is_futures)
    return [
        {
            'timestamp': datetime.fromtimestamp(trade['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
            'price': float(trade['price']),
            'volume': float(trade['qty']),
            'side': 'buy' if trade['isBuyerMaker'] else 'sell'
        }
        for trade in trades
    ]

# Fetch order book data (spot or futures)
def get_order_book(symbol="BTCUSDT", limit=1000, is_futures=False):
    endpoint = "/api/v3/depth" if not is_futures else "/fapi/v1/depth"
    params = {"symbol": symbol, "limit": limit}
    order_book = fetch_binance_data(endpoint, params, is_futures)
    return {
        'bids': [[float(price), float(qty)] for price, qty in order_book['bids']],
        'asks': [[float(price), float(qty)] for price, qty in order_book['asks']]
    }

# Attribute calculation functions
def calculate_bid_ask_spread(order_book):
    return order_book['asks'][0][0] - order_book['bids'][0][0]

def calculate_order_book_depth(order_book, levels=10):
    bid_depth = sum(volume for _, volume in order_book['bids'][:levels])
    ask_depth = sum(volume for _, volume in order_book['asks'][:levels])
    return bid_depth, ask_depth

def calculate_order_book_imbalance(order_book, levels=10):
    bid_volume = sum(volume for _, volume in order_book['bids'][:levels])
    ask_volume = sum(volume for _, volume in order_book['asks'][:levels])
    total_volume = bid_volume + ask_volume
    return (bid_volume - ask_volume) / total_volume if total_volume > 0 else 0

def calculate_vwap(trades):
    total_value = sum(trade['price'] * trade['volume'] for trade in trades)
    total_volume = sum(trade['volume'] for trade in trades)
    return total_value / total_volume if total_volume > 0 else 0

def calculate_realized_volatility(trades):
    prices = [trade['price'] for trade in trades]
    returns = np.diff(np.log(prices))
    return np.std(returns) * np.sqrt(252 * 24 * 60) if len(returns) > 0 else 0

def calculate_market_impact(trades):
    largest_trade_idx = np.argmax([trade['volume'] for trade in trades])
    if largest_trade_idx < len(trades) - 1:
        return trades[largest_trade_idx + 1]['price'] - trades[largest_trade_idx]['price']
    return 0

def calculate_order_flow(trades):
    buy_volume = sum(trade['volume'] for trade in trades if trade['side'] == 'buy')
    sell_volume = sum(trade['volume'] for trade in trades if trade['side'] == 'sell')
    return buy_volume - sell_volume

# Analyze market (spot or futures)
def analyze_market(symbol="BTCUSDT", limit=1000, is_futures=False):
    order_book = get_order_book(symbol, limit, is_futures)
    trades = get_trades(symbol, limit, is_futures)
    
    results = {
        'Bid-Ask Spread': {
            'value': calculate_bid_ask_spread(order_book),
            'explanation': "The difference between the highest buy price and lowest sell price. A smaller spread means lower trading costs and higher liquidity."
        },
        'Order Book Depth (Bids, Asks)': {
            'value': calculate_order_book_depth(order_book),
            'explanation': "Total volume of buy (bids) and sell (asks) orders in the top 10 levels. Shows how much can be traded without moving the price much."
        },
        'Order Book Imbalance': {
            'value': calculate_order_book_imbalance(order_book),
            'explanation': "Compares buy vs. sell volume. Positive means more buying pressure; negative means more selling pressure."
        },
        'VWAP': {
            'value': calculate_vwap(trades),
            'explanation': "Volume-weighted average price of recent trades. A benchmark for what traders paid on average."
        },
        'Realized Volatility': {
            'value': calculate_realized_volatility(trades),
            'explanation': "Measures price swings over time. Higher values mean more risk and opportunity for price changes."
        },
        'Market Impact': {
            'value': calculate_market_impact(trades),
            'explanation': "Price change after the largest trade. Shows how much trades affect the market."
        },
        'Net Order Flow': {
            'value': calculate_order_flow(trades),
            'explanation': "Net difference between buy and sell volumes. Positive suggests bullish sentiment; negative suggests bearish."
        }
    }
    return results

# Flask routes
@app.route('/')
def spot():
    try:
        results = analyze_market(is_futures=False)
        return render_template('index.html', results=results, market_type="Spot")
    except Exception as e:
        return f"Error: {e}"

@app.route('/futures')
def futures():
    try:
        results = analyze_market(is_futures=True, limit=1000)
        return render_template('index.html', results=results, market_type="Futures")
    except Exception as e:
        return f"Error: {e}"

@app.route('/compare')
def compare():
    try:
        spot_results = analyze_market(is_futures=False)
        futures_results = analyze_market(is_futures=True, limit=1000)
        return render_template('compare.html', spot_results=spot_results, futures_results=futures_results)
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=4200)