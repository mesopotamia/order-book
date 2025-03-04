import json
import requests

def fetch_orderbook():
    """Fetch the BTC/USDT order book from Binance API."""
    url = "https://binance.com/api/v3/depth"
    params = {"symbol": "BTCUSDT", "limit": 5000}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching order book: {e}")
        return None

def analyze_orderbook(orderbook_json):
    """Analyze the order book and return analysis result with rationale."""
    if not orderbook_json or "bids" not in orderbook_json or "asks" not in orderbook_json:
        return json.dumps({"error": "Invalid order book data"}, indent=2), None
    
    # Parse bids and asks
    bids = [(float(price), float(qty)) for price, qty in orderbook_json["bids"]]
    asks = [(float(price), float(qty)) for price, qty in orderbook_json["asks"]]
    
    # Current price indicators
    top_bid = bids[0][0]
    top_ask = asks[0][0]
    spread = top_ask - top_bid
    
    # Near-market range: ±$10 from top bid
    near_min = top_bid - 10
    near_max = top_bid + 10
    
    # Near-market volumes
    near_bid_volume = sum(qty for price, qty in bids if price >= near_min)
    near_ask_volume = sum(qty for price, qty in asks if price <= near_max)
    
    # Total volumes
    total_bid_volume = sum(qty for _, qty in bids)
    total_ask_volume = sum(qty for _, qty in asks)
    
    # Top order sizes
    top_bid_size = bids[0][1]
    top_ask_size = asks[0][1]
    
    # Bullishness score calculation
    near_ratio = min(near_bid_volume / max(near_ask_volume, 0.001), 10)
    near_score = min(near_ratio * 2, 10)
    
    total_ratio = min(total_bid_volume / max(total_ask_volume, 0.001), 5)
    total_score = min(total_ratio * 1, 5)
    
    top_ratio = min(top_bid_size / max(top_ask_size, 0.001), 5)
    top_score = min(top_ratio * 0.5, 2.5)
    
    raw_score = near_score * 0.7 + total_score * 0.15 + top_score * 0.15
    bullishness = max(1, min(round(raw_score), 10))
    
    # Analysis result
    result = {
        "bullishness_score": bullishness,
        "current_price": round(top_bid, 2),
        "spread": spread,
        "near_bid_volume": round(near_bid_volume, 5),
        "near_ask_volume": round(near_ask_volume, 5),
        "total_bid_volume": round(total_bid_volume, 5),
        "total_ask_volume": round(total_ask_volume, 5),
        "top_bid_size": top_bid_size,
        "top_ask_size": top_ask_size,
        "last_update_id": orderbook_json["lastUpdateId"]
    }
    
    # Rationale in Markdown format
    rationale = f"""# Rationale for Order Book Analysis

## Bullishness Score Explanation
The bullishness score (1-10) is a weighted combination of three ratios:
- **Near-market bid-to-ask ratio (70%)**: Measures buying vs. selling pressure within ±$10 of the top bid.
- **Total bid-to-ask volume ratio (15%)**: Reflects overall demand vs. supply across the entire order book.
- **Top bid-to-ask size ratio (15%)**: Indicates aggressive buying intent at the top of the book.

### Current Calculation
- **Near-market ratio**: {near_ratio:.2f} (capped at 10), scaled to {near_score:.2f}. Weight: 70%.
- **Total volume ratio**: {total_ratio:.2f} (capped at 5), scaled to {total_score:.2f}. Weight: 15%.
- **Top order ratio**: {top_ratio:.2f} (capped at 5), scaled to {top_score:.2f}. Weight: 15%.
- **Final Score**: ({near_score:.2f} × 0.7) + ({total_score:.2f} × 0.15) + ({top_score:.2f} × 0.15) = {raw_score:.2f}, rounded and clamped to **{bullishness}**.

## Near-Market Volume Explanation
Near-market volumes are sums of bid and ask quantities within ±$10 of the top bid ({top_bid:.2f} USDT):
- **Bids**: From {near_min:.2f} USDT and up, totaling **{near_bid_volume:.5f} BTC**.
- **Asks**: Up to {near_max:.2f} USDT, totaling **{near_ask_volume:.5f} BTC**.

## Total Volume Explanation
Total volumes are the sums of all bid and ask quantities in the order book:
- **Total Bids**: **{total_bid_volume:.5f} BTC**
- **Total Asks**: **{total_ask_volume:.5f} BTC**

## Top Order Explanation
Top order sizes are the quantities at the highest bid and lowest ask:
- **Top Bid**: **{top_bid_size:.5f} BTC** at {top_bid:.2f} USDT
- **Top Ask**: **{top_ask_size:.5f} BTC** at {top_ask:.2f} USDT

## Score Interpretation
How to interpret the bullishness score:
- **8-10**: Strong bullishness (buying pressure dominates).
- **4-7**: Neutral to mild bullishness or bearishness.
- **1-3**: Strong bearishness (selling pressure dominates).

**Current Score**: {bullishness}
"""
    
    return json.dumps(result, indent=2), rationale

def main():
    orderbook_data = fetch_orderbook()
    if orderbook_data:
        analysis_result, rationale = analyze_orderbook(orderbook_data)
        print("Analysis Result:\n", analysis_result)
        
        # Export rationale to rationale.md
        with open("order_book_rationale.md", "w") as f:
            f.write(rationale)
        print("Rationale exported to 'rationale.md'.")
    else:
        print("Failed to fetch order book data.")

if __name__ == "__main__":
    main()