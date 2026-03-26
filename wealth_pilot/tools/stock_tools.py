"""
Stock Tools — FunctionTools for fetching live market data
"""

import json
import yfinance as yf


def fetch_stock_price(ticker: str) -> str:
    """Fetches the current stock price and key financial metrics for a given ticker symbol.

    Args:
        ticker: The stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'MSFT').

    Returns:
        JSON string with price, market cap, P/E ratio, and 52-week range.
    """
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        return json.dumps({
            "ticker": ticker.upper(),
            "price": info.get("currentPrice") or info.get("regularMarketPrice", "N/A"),
            "previous_close": info.get("previousClose", "N/A"),
            "market_cap": info.get("marketCap", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "forward_pe": info.get("forwardPE", "N/A"),
            "dividend_yield": info.get("dividendYield", "N/A"),
            "52w_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52w_low": info.get("fiftyTwoWeekLow", "N/A"),
            "50d_avg": info.get("fiftyDayAverage", "N/A"),
            "200d_avg": info.get("twoHundredDayAverage", "N/A"),
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data for {ticker}: {str(e)}"})


def get_company_info(ticker: str) -> str:
    """Fetches company overview and background information for a given ticker symbol.

    Args:
        ticker: The stock ticker symbol (e.g., 'AAPL', 'GOOGL').

    Returns:
        JSON string with company name, sector, industry, and business summary.
    """
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        summary = info.get("longBusinessSummary", "N/A")
        if isinstance(summary, str) and len(summary) > 500:
            summary = summary[:500] + "..."

        return json.dumps({
            "ticker": ticker.upper(),
            "name": info.get("longName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "employees": info.get("fullTimeEmployees", "N/A"),
            "website": info.get("website", "N/A"),
            "summary": summary,
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch info for {ticker}: {str(e)}"})