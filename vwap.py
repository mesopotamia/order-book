import requests
import numpy as np
from datetime import datetime

# Function to fetch data from Binance API
def fetch_binance_data(endpoint, params):
    url = f"https://binance.com{endpoint}"
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()  # Raise an error if the request fails
    return response.json()

# Fetch trades data
def get_trades(symbol="BTCUSDT", limit=5000):
    endpoint = "/api/v3/trades"
    params = {"symbol": symbol, "limit": limit}
    trades = fetch_binance_data(endpoint, params)
    # Convert to a format we can use
    formatted_trades = [
        {
            'timestamp': datetime.fromtimestamp(trade['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
            'price': float(trade['price']),
            'volume': float(trade['qty']),
            'side': 'buy' if trade['isBuyerMaker'] else 'sell'  # isBuyerMaker=True means buyer-initiated
        }
        for trade in trades
    ]
    return formatted_trades

# Fetch order book data
def get_order_book(symbol="BTCUSDT", limit=5000):
    endpoint = "/api/v3/depth"
    params = {"symbol": symbol, "limit": limit}
    order_book = fetch_binance_data(endpoint, params)
    # Convert to a format we can use: [[price, volume], ...]
    formatted_order_book = {
        'bids': [[float(price), float(qty)] for price, qty in order_book['bids']],
        'asks': [[float(price), float(qty)] for price, qty in order_book['asks']]
    }
    return formatted_order_book

# 1. Bid-Ask Spread
def calculate_bid_ask_spread(order_book):
    best_bid = order_book['bids'][0][0]  # Highest bid price
    best_ask = order_book['asks'][0][0]  # Lowest ask price
    spread = best_ask - best_bid
    return spread

# 2. Order Book Depth
def calculate_order_book_depth(order_book, levels=10):  # Using 10 levels for more granularity
    bid_depth = sum(volume for _, volume in order_book['bids'][:levels])
    ask_depth = sum(volume for _, volume in order_book['asks'][:levels])
    return bid_depth, ask_depth

# 3. Order Book Imbalance
def calculate_order_book_imbalance(order_book, levels=10):
    bid_volume = sum(volume for _, volume in order_book['bids'][:levels])
    ask_volume = sum(volume for _, volume in order_book['asks'][:levels])
    total_volume = bid_volume + ask_volume
    imbalance = (bid_volume - ask_volume) / total_volume if total_volume > 0 else 0
    return imbalance

# 4. Volume-Weighted Average Price (VWAP)
def calculate_vwap(trades):
    total_value = sum(trade['price'] * trade['volume'] for trade in trades)
    total_volume = sum(trade['volume'] for trade in trades)
    vwap = total_value / total_volume if total_volume > 0 else 0
    return vwap

# 5. Realized Volatility
def calculate_realized_volatility(trades):
    prices = [trade['price'] for trade in trades]
    returns = np.diff(np.log(prices))  # Log returns
    volatility = np.std(returns) * np.sqrt(252 * 24 * 60)  # Annualized, assuming minute-level data
    return volatility if len(returns) > 0 else 0

# 6. Market Impact (price change after largest trade)
def calculate_market_impact(trades):
    largest_trade_idx = np.argmax([trade['volume'] for trade in trades])
    if largest_trade_idx < len(trades) - 1:
        price_before = trades[largest_trade_idx]['price']
        price_after = trades[largest_trade_idx + 1]['price']
        impact = price_after - price_before
        return impact
    return 0

# 7. Order Flow
def calculate_order_flow(trades):
    buy_volume = sum(trade['volume'] for trade in trades if trade['side'] == 'buy')
    sell_volume = sum(trade['volume'] for trade in trades if trade['side'] == 'sell')
    net_order_flow = buy_volume - sell_volume
    return net_order_flow

# Main function to compute all attributes
def analyze_market(symbol="BTCUSDT", limit=5000):
    # Fetch data
    order_book = get_order_book(symbol, limit)
    trades = get_trades(symbol, limit)
    
    # Compute attributes
    results = {
        'Bid-Ask Spread': calculate_bid_ask_spread(order_book),
        'Order Book Depth (Bids, Asks)': calculate_order_book_depth(order_book),
        'Order Book Imbalance': calculate_order_book_imbalance(order_book),
        'VWAP': calculate_vwap(trades),
        'Realized Volatility': calculate_realized_volatility(trades),
        'Market Impact': calculate_market_impact(trades),
        'Net Order Flow': calculate_order_flow(trades)
    }
    return results

# Run the analysis
if __name__ == "__main__":
    try:
        results = analyze_market("BTCUSDT", 5000)
        for attribute, value in results.items():
            print(f"{attribute}: {value}")
    except Exception as e:
        print(f"Error: {e}")