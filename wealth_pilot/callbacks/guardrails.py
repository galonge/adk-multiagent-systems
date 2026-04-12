"""
Guardrail Callbacks — Validation, disclaimers, and audit logging
"""

import logging
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger("WealthPilot")


# ── BEFORE AGENT — Audit Logging ─────────────────────
def audit_log_before_agent(callback_context: CallbackContext) -> None:
    """Logs every agent invocation for audit trail."""
    agent_name = callback_context.agent_name
    print(f"🔍 [AUDIT] Agent '{agent_name}' invoked")


# ── AFTER MODEL — Financial Disclaimer ───────────────
def add_disclaimer_after_model(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> Optional[LlmResponse]:
    """Logs after every model response. Returns None to pass through."""
    agent_name = callback_context.agent_name
    print(f"📋 [DISCLAIMER] Model response from '{agent_name}'")
    return None  # Don't modify — let it pass through


# ── BEFORE TOOL — Ticker Validation ──────────────────
def validate_ticker_before_tool(
    tool: BaseTool,
    args: dict,
    tool_context: ToolContext,
) -> Optional[dict]:
    """Validates stock ticker symbols before tool execution.

    Returns None to allow the tool to proceed,
    or a dict with an error message to block execution.
    """
    tool_name = tool.name

    # Only validate stock-related tools
    if tool_name not in ("fetch_stock_price", "get_company_info"):
        return None

    ticker = args.get("ticker", "")

    if not ticker:
        print("🚫 [GUARDRAIL] Empty ticker rejected")
        return {"error": "Ticker symbol cannot be empty"}

    if not ticker.replace(".", "").replace("-", "").isalpha():
        print(f"🚫 [GUARDRAIL] Invalid ticker rejected: {ticker}")
        return {"error": f"Invalid ticker: '{ticker}'. Must be letters only."}

    if len(ticker) > 5:
        print(f"🚫 [GUARDRAIL] Ticker too long: {ticker}")
        return {"error": f"Invalid ticker: '{ticker}'. Max 5 characters."}

    print(f"✅ [GUARDRAIL] Ticker '{ticker.upper()}' validated")
    return None  # Valid — let the tool proceed


# ── AFTER AGENT — Save to Memory ─────────────────────
async def save_to_memory_after_agent(callback_context: CallbackContext) -> None:
    """saves the current session to memory after each agent run."""
    agent_name = callback_context.agent_name
    await callback_context.add_session_to_memory()
    print(f"🧠 [MEMORY] Session saved to memory after '{agent_name}'")
    return None
