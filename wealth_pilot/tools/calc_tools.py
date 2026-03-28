"""
calculation tools — financial math and portfolio calculations
"""

import json


def calculate_compound_returns(
    principal: float,
    annual_return_pct: float,
    years: int,
) -> str:
    """Calculates compound returns on an investment over time.

    Args:
        principal: Initial investment amount in USD.
        annual_return_pct: Expected annual return as a percentage (e.g., 8.0 for 8%).
        years: Number of years to project.

    Returns:
        JSON with yearly breakdown, final balance, and total return.
    """
    yearly_breakdown = []
    balance = principal

    for year in range(1, years + 1):
        interest = balance * (annual_return_pct / 100)
        balance += interest
        yearly_breakdown.append({
            "year": year,
            "starting_balance": round(balance - interest, 2),
            "interest_earned": round(interest, 2),
            "ending_balance": round(balance, 2),
        })

    return json.dumps({
        "principal": principal,
        "annual_return_pct": annual_return_pct,
        "years": years,
        "final_balance": round(balance, 2),
        "total_gain": round(balance - principal, 2),
        "total_return_pct": round((balance - principal) / principal * 100, 2),
        "yearly_breakdown": yearly_breakdown,
    })


def calculate_portfolio_allocation(
    budget: float,
    allocations_json: str,
) -> str:
    """Calculates dollar amounts from percentage allocations.

    Args:
        budget: Total investment budget in USD.
        allocations_json: JSON string mapping tickers to percentages.
            Example: '{"AAPL": 40, "GOOGL": 35, "BND": 25}'

    Returns:
        JSON with per-position dollar amounts and validation.
    """
    try:
        allocations = json.loads(allocations_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON in allocations_json"})

    total_pct = sum(allocations.values())
    result = {}
    for ticker, pct in allocations.items():
        result[ticker] = {"percentage": pct, "dollar_amount": round(budget * pct / 100, 2)}

    return json.dumps({
        "budget": budget,
        "total_allocated_pct": total_pct,
        "is_valid": abs(total_pct - 100) < 0.01,
        "positions": result,
        "warning": None if abs(total_pct - 100) < 0.01 else f"Allocations sum to {total_pct}%, not 100%",
    })