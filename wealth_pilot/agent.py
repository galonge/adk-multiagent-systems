"""
WealthPilot — AI Wealth Advisor
Built with Google Agent Development Kit (ADK)
"""

# enable agentops
# import agentops
# agentops.init()

from google.adk.agents import LlmAgent, SequentialAgent
from .tools.stock_tools import (
    fetch_stock_price,
    get_company_info,
    save_user_preferences,
)
from .callbacks.guardrails import (
    audit_log_before_agent,
    add_disclaimer_after_model,
    validate_ticker_before_tool,
    save_to_memory_after_agent,
)
from google.adk.tools.load_memory_tool import LoadMemoryTool
from .tools.calc_tools import calculate_compound_returns, calculate_portfolio_allocation
from .tools.report_tools import save_portfolio_report
from google.genai import types

# ── Stock Analyst ─────────────────────────────────────
# note: model is the V1 default — V2 overrides via model_switcher_callback
stock_analyst = LlmAgent(
    name="StockAnalyst",
    model="gemini-2.5-flash",
    description="Analyzes individual stocks by fetching live market data.",
    instruction="""You are a Stock Analyst at WealthPilot.

Your job is to analyze individual stocks using your tools.
When asked about a stock:
1. Use fetch_stock_price to get current price and key metrics.
2. Use get_company_info to get company background.
3. Provide a clear, concise analysis covering:
   - Current price and valuation (P/E ratio)
   - 52-week range context (is it near highs or lows?)
   - Company sector and business summary
   - A brief outlook (bullish/bearish/neutral)

Keep your analysis factual and data-driven.
Do NOT make specific buy/sell recommendations.""",
    tools=[fetch_stock_price, get_company_info],
    before_tool_callback=validate_ticker_before_tool,
)

# ── Portfolio Advisor ─────────────────────────────────
# note: model is the V1 default — V2 overrides via model_switcher_callback
portfolio_advisor = LlmAgent(
    name="PortfolioAdvisor",
    model="gemini-2.5-flash",
    description="Advises on portfolio allocation based on user preferences.",
    instruction="""You are a Portfolio Advisor at WealthPilot.
Your job is to recommend portfolio allocations based on:
- The stock analyses provided by StockAnalyst
- The user's preferences from session state (check for: risk_tolerance, investment_budget, investment_horizon)

Guidelines by risk tolerance:
- Conservative: max 40% stocks, 60%+ bonds/stable assets
- Moderate: 50-70% stocks, 30-50% bonds
- Aggressive: 70-90% stocks, 10-30% bonds

Use your tools:
- calculate_compound_returns: to project growth over the investment horizon
- calculate_portfolio_allocation: to compute dollar amounts for each position

Always explain your reasoning.""",
    tools=[calculate_compound_returns, calculate_portfolio_allocation],
)

# ── Report Generator ──────────────────────────────────
# note: model is the V1 default — V2 overrides via model_switcher_callback
report_generator = LlmAgent(
    name="ReportGenerator",
    model="gemini-2.5-flash",
    description="Generates formatted portfolio analysis reports.",
    instruction="""You are the Report Generator at WealthPilot.
Create a comprehensive portfolio report including:
1. Executive Summary
2. Stock Analysis
3. Recommended Allocation
4. Risk Assessment
5. Save the report as a versioned artifact using save_portfolio_report tool

Format your output in clean Markdown.""",
    tools=[save_portfolio_report],
)


# ── Analysis Pipeline ─────────────────────────────────
analysis_pipeline = SequentialAgent(
    name="AnalysisPipeline",
    description="Runs the full analysis: analyze stocks → advise → report.",
    sub_agents=[stock_analyst, portfolio_advisor, report_generator],
)


# ── Root Agent ────────────────────────────────────────
# default to Flash so the app works even when Pro is overloaded.
# V2 model switcher overrides this per-session via model_switcher_callback.
root_agent = LlmAgent(
    name="WealthPilot",
    model="gemini-2.5-flash",
    description="AI Wealth Advisor — analyzes stocks and builds portfolios.",
    instruction="""You are **WealthPilot**, an AI Wealth Advisor.

You help users analyze stocks and build investment portfolios.
You have a team of specialist agents to help you:
- **AnalysisPipeline**: Full sequential flow (analyze → advise → report)

## Conversation Flow
1. Greet the user warmly
2. Use LoadMemoryTool to check for any past preferences or conversations with this user
3. Ask about their investment goals, budget, risk tolerance
4. Save Preferences using save_user_preferences tool once you have the info
5. When they want analysis, transfer to AnalysisPipeline

Be conversational, warm, and professional.
Always include: "This is AI-generated analysis, not financial advice." """,
    sub_agents=[analysis_pipeline],
    before_agent_callback=audit_log_before_agent,
    after_model_callback=add_disclaimer_after_model,
    tools=[save_user_preferences, LoadMemoryTool()],
    after_agent_callback=save_to_memory_after_agent,
    generate_content_config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=2048,
        )
    ),
)
