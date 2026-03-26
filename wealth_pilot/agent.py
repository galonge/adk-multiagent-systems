"""
WealthPilot — AI Wealth Advisor
Built with Google Agent Development Kit (ADK)
"""

from google.adk.agents import LlmAgent, SequentialAgent
from .tools.stock_tools import fetch_stock_price, get_company_info

# ── Stock Analyst ─────────────────────────────────────
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
)

# ── Portfolio Advisor ─────────────────────────────────
portfolio_advisor = LlmAgent(
    name="PortfolioAdvisor",
    model="gemini-2.5-flash",
    description="Advises on portfolio allocation based on user preferences.",
    instruction="""You are a Portfolio Advisor at WealthPilot.
Your job is to recommend portfolio allocations based on:
- The stock analyses provided by StockAnalyst
- The user's risk tolerance and investment horizon

Guidelines by risk tolerance:
- Conservative: max 40% stocks, 60%+ bonds/stable assets
- Moderate: 50-70% stocks, 30-50% bonds
- Aggressive: 70-90% stocks, 10-30% bonds

Always explain your reasoning.""",
)

# ── Report Generator ──────────────────────────────────
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

Format your output in clean Markdown.""",
)


# ── Analysis Pipeline ─────────────────────────────────
analysis_pipeline = SequentialAgent(
    name="AnalysisPipeline",
    description="Runs the full analysis: analyze stocks → advise → report.",
    sub_agents=[stock_analyst, portfolio_advisor, report_generator],
)


# ── Root Agent ────────────────────────────────────────
root_agent = LlmAgent(
    name="WealthPilot",
    model="gemini-2.5-pro",
    description="AI Wealth Advisor — analyzes stocks and builds portfolios.",
    instruction="""You are **WealthPilot**, an AI Wealth Advisor.

You help users analyze stocks and build investment portfolios.
You have a team of specialist agents to help you:
- **AnalysisPipeline**: Full sequential flow (analyze → advise → report)

## Conversation Flow
1. Greet the user warmly
2. Ask about their investment goals, budget, risk tolerance
3. When they want analysis, transfer to AnalysisPipeline

Be conversational, warm, and professional.
Always include: "This is AI-generated analysis, not financial advice." """,
    sub_agents=[analysis_pipeline],
)