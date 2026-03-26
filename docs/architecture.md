# WealthPilot — Architecture

> **WealthPilot** is an AI Wealth Advisor built with Google's Agent Development Kit (ADK).
> It analyzes stocks, builds portfolios, optimizes for risk, and generates PDF reports —
> all powered by a team of specialized AI agents working together.

---

## What We're Building

```mermaid
graph TD
    User([👤 User]) -->|"Analyze AAPL for $50K,<br/>moderate risk"| WP

    subgraph WP["WealthPilot — Root Agent"]
        direction TB
        WP_desc["Orchestrates the team<br/>Model: gemini-2.5-pro | Planning: ReAct"]
    end

    WP --> SA
    WP --> PA
    WP --> RG

    SA["📈 StockAnalyst<br/>Fetches live stock data<br/>& analyzes fundamentals"]
    PA["💼 PortfolioAdvisor<br/>Calculates allocations<br/>& projected returns"]
    RG["📄 ReportGenerator<br/>Builds a PDF portfolio<br/>report as an artifact"]

    SA -->|"stock analysis"| PA
    PA -->|"allocation plan"| RG
    RG -->|"📊 PDF Report"| User

    style WP fill:#1a1a2e,color:#fff,stroke:#4ade80
    style SA fill:#16213e,color:#fff,stroke:#4cc9f0
    style PA fill:#16213e,color:#fff,stroke:#f72585
    style RG fill:#16213e,color:#fff,stroke:#fca311
```

---

## How a Request Flows

```mermaid
sequenceDiagram
    actor User
    participant WP as WealthPilot<br/>(Root Agent)
    participant SA as StockAnalyst
    participant PA as PortfolioAdvisor
    participant RG as ReportGenerator

    User->>WP: ① "Analyze AAPL, $50K, moderate risk"

    Note over WP: ② Plans steps using ReAct reasoning

    WP->>SA: ③ "Get me the data on AAPL"
    SA->>SA: calls fetch_stock_price()
    SA-->>WP: returns price, P/E, 52-week range

    WP->>PA: ④ "Build a portfolio with this data"
    PA->>PA: calls calculate_allocation()
    PA->>PA: calls calculate_compound_growth()
    PA-->>WP: returns 60% AAPL / 40% Bonds → $67K in 5yr

    WP->>RG: ⑤ "Create the final report"
    RG->>RG: calls save_portfolio_report()
    RG-->>User: ⑥ 📊 PDF Report delivered
```

---

## ADK Components Used

Each row maps an ADK concept to how WealthPilot uses it.

| ADK Concept | What It Does | WealthPilot Usage |
|---|---|---|
| **LlmAgent** | AI agent with a model + instructions | WealthPilot, StockAnalyst, PortfolioAdvisor, ReportGenerator |
| **SequentialAgent** | Runs agents in order | AnalysisPipeline (Analyst → Advisor → Report) |
| **ParallelAgent** | Runs agents simultaneously | Analyze multiple stocks at once |
| **LoopAgent** | Repeats until a condition is met | Optimize allocation until risk tolerance is satisfied |
| **FunctionTool** | Python function an agent can call | `fetch_stock_price`, `calculate_compound_growth`, `save_portfolio_report` |
| **AgentTool** | Use one agent as a tool for another | StockAnalyst available as a tool to PortfolioAdvisor |
| **Callbacks** | Hooks that run before/after agent/model/tool | Ticker validation, financial disclaimers, audit logging |
| **Session & State** | Conversation tracking + key-value storage | Store risk tolerance, budget, preferences per conversation |
| **Memory** | Cross-session recall | Remember user preferences across conversations |
| **Artifacts** | File storage for generated outputs | Save PDF portfolio reports |
| **Planning (ReAct)** | Multi-step reasoning and tool use | Root agent decomposes complex requests into steps |

---

## Agent Types at a Glance

```mermaid
graph LR
    subgraph Sequential["SequentialAgent"]
        direction LR
        S1["Agent A"] --> S2["Agent B"] --> S3["Agent C"]
    end

    subgraph Parallel["ParallelAgent"]
        direction LR
        P1["Agent A"]
        P2["Agent B"]
        P3["Agent C"]
    end

    subgraph Loop["LoopAgent"]
        direction LR
        L1["Proposer"] --> L2["Checker"]
        L2 -->|"retry"| L1
    end

    style Sequential fill:#16213e,color:#fff,stroke:#4ade80
    style Parallel fill:#16213e,color:#fff,stroke:#f72585
    style Loop fill:#16213e,color:#fff,stroke:#fca311
```

- **Sequential** — Agents run one after another. Output of A feeds into B.
- **Parallel** — All agents run at the same time. Results are collected together.
- **Loop** — Agents repeat in a cycle until a condition is satisfied.

---

## Lecture Guide (Section 2)

| Lecture | Topic | What We'll Cover |
|-------|-------|-----------------|
| 2.1 | Section Intro | Architecture overview (this doc) |
| 2.2 | Agents & Models | Root agent + 3 sub-agents |
| 2.3 | Tools | `stock_tools.py` — live stock data via yfinance |
| 2.4 | Callbacks | Ticker validation, disclaimers, audit log |
| 2.5 | Session, State & Events | User preferences in state |
| 2.6 | Memory | Cross-session recall |
| 2.7 | Code Execution | `calc_tools.py` — compound returns, allocations |
| 2.8 | Artifacts | `report_tools.py` — PDF portfolio report |
| 2.9 | Planning | ReAct planner for multi-step requests |
| 2.10 | Parallel & Loop Agents | Multi-stock fetch + risk optimization loop |
| 2.11 | Runner & AgentTool | Programmatic runner with all services |
| 2.12 | Putting It Together | Final polish, E2E demo |

---

## Project Structure

```
wealth_pilot/
├── agent.py                  # All agents + orchestration
├── tools/
│   ├── stock_tools.py        # fetch_stock_price, get_company_info
│   ├── calc_tools.py         # compound returns, allocation math
│   └── report_tools.py       # save_portfolio_report (PDF artifact)
├── callbacks/
│   └── guardrails.py         # ticker validation, disclaimers, audit
├── docs/                     # Per-video guides + extensions
├── main.py                   # FastAPI production server
├── .env                      # GOOGLE_API_KEY
└── pyproject.toml            # Dependencies
```
