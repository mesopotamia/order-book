import requests
import json
from statistics import mean, stdev

def fetch_trades():
    """Fetch recent BTC/USDT trades from Binance API."""
    url = "https://binance.com/api/v3/trades"
    params = {"symbol": "BTCUSDT", "limit": 5000}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching trades: {e}")
        return None

def analyze_trades(trades):
    """Analyze trades and return summary with rationale."""
    if not trades:
        return json.dumps({"error": "No trade data available"}, indent=2), None
    
    # Basic volume metrics
    total_volume = sum(float(trade["qty"]) for trade in trades)
    buy_volume = sum(float(trade["qty"]) for trade in trades if not trade["isBuyerMaker"])
    sell_volume = sum(float(trade["qty"]) for trade in trades if trade["isBuyerMaker"])
    
    # Market buy proportion
    market_buy_count = sum(1 for trade in trades if not trade["isBuyerMaker"])
    total_trades = len(trades)
    market_buy_ratio = market_buy_count / total_trades if total_trades > 0 else 0
    
    # Average trade sizes
    buy_count = market_buy_count
    sell_count = total_trades - buy_count
    avg_buy_size = buy_volume / buy_count if buy_count > 0 else 0
    avg_sell_size = sell_volume / sell_count if sell_count > 0 else 0
    
    # Bullishness score
    volume_ratio = min(buy_volume / max(sell_volume, 0.001), 10)
    volume_score = min(volume_ratio * 2, 10)
    market_score = min(market_buy_ratio * 10, 10)
    size_ratio = min(avg_buy_size / max(avg_sell_size, 0.001), 5)
    size_score = min(size_ratio * 2, 5)
    raw_score = volume_score * 0.5 + market_score * 0.3 + size_score * 0.2
    bullishness = max(1, min(round(raw_score), 10))
    
    # Retail vs. Professional Assessment
    trade_sizes = [float(trade["qty"]) for trade in trades]
    avg_trade_size = mean(trade_sizes)
    size_std = stdev(trade_sizes) if len(trade_sizes) > 1 else 0
    large_trade_count = sum(1 for size in trade_sizes if size >= 1.0)  # Threshold for "large"
    timestamp_counts = {}
    for trade in trades:
        timestamp_counts[trade["time"]] = timestamp_counts.get(trade["time"], 0) + 1
    max_trades_per_ms = max(timestamp_counts.values()) if timestamp_counts else 1
    
    # Heuristics for retail vs. professional
    if avg_trade_size < 0.1 and size_std < 0.5 and max_trades_per_ms <= 5:
        trader_type = "Retail"
        trader_explanation = (
            f"- **Average trade size**: {avg_trade_size:.5f} BTC (<0.1 BTC, typical for retail).\n"
            f"- **Size variability**: Std dev {size_std:.5f} BTC (low, suggesting small, consistent trades).\n"
            f"- **Max trades per millisecond**: {max_trades_per_ms} (low frequency, not algorithmic)."
        )
    elif avg_trade_size >= 1.0 or large_trade_count > 10 or max_trades_per_ms > 20:
        trader_type = "Professional/Institutional"
        trader_explanation = (
            f"- **Average trade size**: {avg_trade_size:.5f} BTC (>=1 BTC or significant).\n"
            f"- **Large trades**: {large_trade_count} trades >= 1 BTC (institutional activity).\n"
            f"- **Max trades per millisecond**: {max_trades_per_ms} (high frequency, likely bots)."
        )
    else:
        trader_type = "Mixed"
        trader_explanation = (
            f"- **Average trade size**: {avg_trade_size:.5f} BTC (moderate, not clearly retail or pro).\n"
            f"- **Size variability**: Std dev {size_std:.5f} BTC (some variation).\n"
            f"- **Max trades per millisecond**: {max_trades_per_ms} (moderate frequency)."
        )
    
    # Summary result
    result = {
        "bullishness_score": bullishness,
        "total_volume": round(total_volume, 5),
        "buy_volume": round(buy_volume, 5),
        "sell_volume": round(sell_volume, 5),
        "market_buy_ratio": round(market_buy_ratio, 3),
        "avg_buy_size": round(avg_buy_size, 5),
        "avg_sell_size": round(avg_sell_size, 5),
        "avg_trade_size": round(avg_trade_size, 5),
        "large_trade_count": large_trade_count,
        "trader_type": trader_type,
        "trade_count": total_trades,
        "last_trade_time": trades[-1]["time"]
    }
    
    # Rationale in Markdown
    rationale = f"""# Trades Rationale for BTC/USDT

## Bullishness Score Explanation
The bullishness score (1-10) reflects buying pressure in recent trades, based on:
- **Buy-to-sell volume ratio (50%)**: Higher buy volume indicates bullishness.
- **Market buy proportion (30%)**: Percentage of trades where buyers were takers (market buys), showing aggressive buying.
- **Average buy-to-sell size ratio (20%)**: Larger buy trades suggest stronger conviction.

### Current Calculation
- **Buy-to-sell volume ratio**: {buy_volume:.5f} BTC / {sell_volume:.5f} BTC = {volume_ratio:.2f} (capped at 10), scaled to {volume_score:.2f}.
- **Market buy proportion**: {market_buy_count} taker buys / {total_trades} trades = {market_buy_ratio:.3f}, scaled to {market_score:.2f}.
- **Avg buy-to-sell size ratio**: {avg_buy_size:.5f} BTC / {avg_sell_size:.5f} BTC = {size_ratio:.2f} (capped at 5), scaled to {size_score:.2f}.
- **Final Score**: ({volume_score:.2f} × 0.5) + ({market_score:.2f} × 0.3) + ({size_score:.2f} × 0.2) = {raw_score:.2f}, rounded to **{bullishness}**.

## Trade Volume Summary
- **Total Volume**: **{total_volume:.5f} BTC** over {total_trades} trades.
- **Buy Volume**: **{buy_volume:.5f} BTC** (market/taker buys).
- **Sell Volume**: **{sell_volume:.5f} BTC** (market/taker sells).

## Market Buy Analysis
- **Market Buy Ratio**: **{market_buy_ratio:.3f}** ({market_buy_count} taker buys out of {total_trades} trades).
- Taker buys (`isBuyerMaker: false`) indicate aggressive buying, lifting offers from the order book.

## Trade Size Analysis
- **Average Buy Size**: **{avg_buy_size:.5f} BTC** across {buy_count} buy trades.
- **Average Sell Size**: **{avg_sell_size:.5f} BTC** across {sell_count} sell trades.
- Larger buy sizes relative to sell sizes suggest stronger buying intent.

## Retail vs. Professional Assessment
Based on trade sizes and frequency:
{trader_explanation}
- **Conclusion**: Likely **{trader_type}** activity dominates these trades.

## Score Interpretation
- **8-10**: Strong bullishness (buyers dominate in volume and aggression).
- **4-7**: Neutral or mild bullishness/bearishness.
- **1-3**: Strong bearishness (sellers dominate).
- **Current Score**: **{bullishness}**
"""
    
    return json.dumps(result, indent=2), rationale

def main():
    trades_data = fetch_trades()
    if trades_data:
        analysis_result, rationale = analyze_trades(trades_data)
        print("Trade Volume Analysis:\n", analysis_result)
        
        # Export rationale to trades_rationale.md
        with open("trades_rationale.md", "w") as f:
            f.write(rationale)
        print("Rationale exported to 'trades_rationale.md'.")
    else:
        print("Failed to fetch trade data.")

if __name__ == "__main__":
    main()