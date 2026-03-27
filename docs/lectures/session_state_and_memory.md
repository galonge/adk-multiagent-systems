# session, state & memory — how agents remember

> **session** is the conversation thread. **state** is the notepad you scribble on during it.
> **memory** is the file cabinet where you store notes from all past conversations.

think of it like a phone call: the session is one call, state is what you jot down
while talking, and memory is your CRM where you log everything after hanging up —
so next time you call, you already know who you're talking to.

---

## how session, state, and memory relate

```mermaid
flowchart TD
    USER(["👤 user"]) --> SS

    subgraph SS["SessionService"]
        direction TB
        SESSION["📞 session<br/>(one conversation thread)"]
        SESSION --> EVENTS["📜 events<br/>(message history)"]
        SESSION --> STATE["📝 state<br/>(key-value scratchpad)"]
    end

    SESSION -->|"session ends"| MS

    subgraph MS["MemoryService"]
        direction TB
        STORE["🧠 long-term knowledge store<br/>(searchable across all sessions)"]
    end

    STORE -->|"agent recalls context"| SESSION

    style SS fill:#1a1a2e,color:#fff,stroke:#4ade80
    style MS fill:#1a1a2e,color:#fff,stroke:#f72585
    style SESSION fill:#16213e,color:#fff,stroke:#4ade80
    style EVENTS fill:#0d1117,color:#fff,stroke:#4cc9f0
    style STATE fill:#0d1117,color:#fff,stroke:#4cc9f0
    style STORE fill:#16213e,color:#fff,stroke:#f72585
    style USER fill:#0d1117,color:#fff,stroke:#fca311
```

---

## session — the conversation container

a session is a single conversation thread between a user and your agent system.
it holds the full history of messages plus a scratchpad for temporary data.

| property | what it holds |
|---|---|
| `id` | unique identifier for this conversation thread |
| `app_name` | which agent app this belongs to |
| `user_id` | which user is chatting |
| `events` | chronological list of messages and actions |
| `state` | key-value scratchpad (see below) |
| `last_update_time` | when the session was last touched |

### session lifecycle

```mermaid
sequenceDiagram
    actor App
    participant SS as SessionService
    participant R as Runner
    participant A as Agent

    App->>SS: ① create_session()
    SS-->>R: session (with state + events)

    App->>R: ② user sends a message
    R->>A: ③ process query (with session context)
    A-->>R: ④ response + state updates

    R->>SS: ⑤ append_event(session, event)
    Note over SS: saves the event + updates state

    R-->>App: ⑥ agent response returned

    App->>SS: ⑦ delete_session() (when done)
```

---

## state — the session's scratchpad

`session.state` is a dictionary of key-value pairs. it lets agents track information
during a conversation without polluting the message history.

### the four prefix scopes

this is the most important concept — **prefixes control how far state reaches**:

| prefix | scope | persists across sessions? | example |
|---|---|---|---|
| *(none)* | this session only | no | `state['risk_tolerance'] = 'moderate'` |
| `user:` | this user, all sessions | yes | `state['user:name'] = 'George'` |
| `app:` | all users, all sessions | yes | `state['app:disclaimer'] = '...'` |
| `temp:` | this invocation only | no (discarded after) | `state['temp:raw_response'] = {...}` |

```mermaid
flowchart LR
    subgraph TEMP["temp: (invocation)"]
        T["lives for one<br/>request-response cycle"]
    end

    subgraph SESSION["no prefix (session)"]
        S["lives for the entire<br/>conversation thread"]
    end

    subgraph USR["user: (cross-session)"]
        U["shared across all<br/>sessions for one user"]
    end

    subgraph APP["app: (global)"]
        A["shared across all<br/>users and sessions"]
    end

    TEMP ~~~ SESSION ~~~ USR ~~~ APP

    style TEMP fill:#0d1117,color:#fff,stroke:#555
    style SESSION fill:#16213e,color:#fff,stroke:#4cc9f0
    style USR fill:#16213e,color:#fff,stroke:#4ade80
    style APP fill:#16213e,color:#fff,stroke:#f72585
```

### how state gets updated

two recommended methods:

| method | how it works |
|---|---|
| `output_key` on `LlmAgent` | automatically saves the agent's response text to a state key |
| `tool_context.state` | read/write state from inside any tool function |

---

## SessionService implementations

ADK provides different backends — pick the one that fits your deployment:

| service | storage | best for |
|---|---|---|
| `InMemorySessionService` | RAM (lost on restart) | local dev and testing |
| `DatabaseSessionService` | SQLite / PostgreSQL | production persistence |
| `VertexAiSessionService` | Google Cloud | managed cloud deployments |

---

## memory — cross-session recall

memory is a **searchable knowledge store** that spans across conversations.
when a session ends, its contents can be ingested into memory. future sessions
can then search that store to recall context from past interactions.

### how memory works

```mermaid
flowchart LR
    S1["📞 session ends"] -->|"add_session_to_memory()"| STORE["🧠 memory store"]
    STORE -->|"agent searches"| S2["📞 new session"]

    style S1 fill:#16213e,color:#fff,stroke:#4ade80
    style STORE fill:#16213e,color:#fff,stroke:#f72585
    style S2 fill:#16213e,color:#fff,stroke:#4ade80
```

### built-in memory tools

| tool | behavior |
|---|---|
| `PreloadMemoryTool` | automatically loads relevant memories at the start of each turn |
| `LoadMemoryTool` | agent decides when to search memory (on-demand) |

### MemoryService implementations

| service | storage | best for |
|---|---|---|
| `InMemoryMemoryService` | RAM (lost on restart) | local dev and testing |
| `VertexAiMemoryService` | Google Cloud Memory Bank | production with managed search |

---

## what we'll build in WealthPilot

| feature | concept | what it does |
|---|---|---|
| risk tolerance tracking | state (no prefix) | stores the user's risk tolerance for the current conversation |
| user preferences | state (`user:` prefix) | remembers the user's name and preferred investment style across sessions |
| conversation recall | memory | recalls past portfolio analyses from previous conversations |

---

## session vs state vs memory — when to use what

| question | use |
|---|---|
| need data for this conversation only? | **state** (no prefix) |
| need data across all conversations for one user? | **state** (`user:` prefix) |
| need data shared across all users? | **state** (`app:` prefix) |
| need temporary scratch data within one request? | **state** (`temp:` prefix) |
| need searchable recall of past conversations? | **memory** |
| need the raw conversation history? | **session.events** |
