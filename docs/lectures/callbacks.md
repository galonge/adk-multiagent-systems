# callbacks — hooks into the agent execution flow

> callbacks let you observe, customize, and control what happens at key moments
> during an agent's execution — without modifying any ADK framework code.

think of them as **airport security checkpoints**: your luggage (data) passes through
scanners (callbacks) at specific points. each checkpoint can inspect, modify, or even
reject items before they continue on their journey.

---

## where callbacks hook in

the diagram below shows every point in the agent execution cycle where you can
attach a callback. there are **6 hooks** organized into **3 pairs**:

```mermaid
flowchart TD
    REQ([" 👤 user request "]) --> BA

    subgraph AGENT["agent execution"]
        direction TB
        BA["🟢 before_agent"] --> LOGIC["agent decides what to do"]
        LOGIC --> BM

        subgraph LLM_CALL["LLM interaction"]
            direction TB
            BM["🔵 before_model"] --> MODEL["🤖 call LLM"]
            MODEL --> AM["🔵 after_model"]
        end

        AM --> BT

        subgraph TOOL_CALL["tool execution"]
            direction TB
            BT["🟣 before_tool"] --> TOOL["🔧 run tool"]
            TOOL --> AT["🟣 after_tool"]
        end

        AT --> AA["🟢 after_agent"]
    end

    AA --> RES(["💬 response to user"])

    style AGENT fill:#1a1a2e,color:#fff,stroke:#4ade80
    style LLM_CALL fill:#16213e,color:#fff,stroke:#4cc9f0
    style TOOL_CALL fill:#16213e,color:#fff,stroke:#f72585
    style BA fill:#0d1117,color:#4ade80,stroke:#4ade80
    style AA fill:#0d1117,color:#4ade80,stroke:#4ade80
    style BM fill:#0d1117,color:#4cc9f0,stroke:#4cc9f0
    style AM fill:#0d1117,color:#4cc9f0,stroke:#4cc9f0
    style BT fill:#0d1117,color:#f72585,stroke:#f72585
    style AT fill:#0d1117,color:#f72585,stroke:#f72585
    style MODEL fill:#0d1117,color:#fff,stroke:#555
    style TOOL fill:#0d1117,color:#fff,stroke:#555
    style LOGIC fill:#0d1117,color:#fff,stroke:#555
    style REQ fill:#0d1117,color:#fff,stroke:#fca311
    style RES fill:#0d1117,color:#fff,stroke:#fca311
```

---

## the three callback categories

| category | callbacks | what they wrap | available on |
|---|---|---|---|
| **agent lifecycle** | `before_agent` / `after_agent` | the agent's entire run | all agent types |
| **LLM interaction** | `before_model` / `after_model` | each call to the LLM | `LlmAgent` only |
| **tool execution** | `before_tool` / `after_tool` | each tool invocation | `LlmAgent` only |

---

## how callbacks control the flow

this is the most powerful part — **the return value decides what happens next**.

### the two paths

| return value | what happens |
|---|---|
| `None` | ✅ proceed normally — the callback just observed or modified in-place |
| **an object** | ⛔ skip/override the step — the returned object replaces the real result |

### decision flow for `before_model`

```mermaid
flowchart LR
    CB["before_model_callback()"] --> CHECK{returns None?}
    CHECK -->|yes| LLM["call the LLM normally"]
    CHECK -->|no| SKIP["use returned LlmResponse\n(LLM call is skipped)"]

    style CB fill:#0d1117,color:#4cc9f0,stroke:#4cc9f0
    style CHECK fill:#16213e,color:#fff,stroke:#fca311
    style LLM fill:#0d1117,color:#4ade80,stroke:#4ade80
    style SKIP fill:#0d1117,color:#f72585,stroke:#f72585
```

### return types for each callback

| callback | return to **skip/override** | use case |
|---|---|---|
| `before_agent` | `types.Content` | skip the agent's logic entirely |
| `after_agent` | `types.Content` | replace the agent's output |
| `before_model` | `LlmResponse` | skip the LLM call (guardrails, cache) |
| `after_model` | `LlmResponse` | modify/replace the LLM response |
| `before_tool` | `dict` | skip tool execution (validation, mocks) |
| `after_tool` | `dict` | modify/replace tool results |

---

## what we'll build in WealthPilot

we'll implement three callbacks in `callbacks/guardrails.py`:

| callback | hook | what it does |
|---|---|---|
| `validate_ticker` | `before_tool` | rejects invalid stock ticker symbols before they reach yfinance |
| `add_disclaimer` | `after_agent` | appends "this is not financial advice" to every agent response |
| `audit_log` | `before_agent` | logs every agent invocation with a timestamp and agent name |

---

## when to use callbacks

| ✅ good fit | ❌ use something else |
|---|---|
| input/output validation | complex multi-step business logic (use agents) |
| logging and audit trails | persistent data storage (use session state) |
| adding disclaimers or safety checks | security policies (use ADK plugins) |
| caching LLM responses | cross-agent communication (use state/memory) |
| blocking disallowed operations | |
| modifying prompts before they hit the LLM | |

---

## quick-reference cheat sheet

| hook | fires | signature (Python) | skip by returning |
|---|---|---|---|
| `before_agent` | before agent runs | `(CallbackContext) → Content \| None` | `types.Content` |
| `after_agent` | after agent finishes | `(CallbackContext) → Content \| None` | `types.Content` |
| `before_model` | before LLM call | `(CallbackContext, LlmRequest) → LlmResponse \| None` | `LlmResponse` |
| `after_model` | after LLM response | `(CallbackContext, LlmResponse) → LlmResponse \| None` | `LlmResponse` |
| `before_tool` | before tool runs | `(CallbackContext, ToolContext) → dict \| None` | `dict` |
| `after_tool` | after tool returns | `(CallbackContext, ToolContext) → dict \| None` | `dict` |
