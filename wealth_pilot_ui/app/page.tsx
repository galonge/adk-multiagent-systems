"use client";

import { useState, useRef, useEffect, useCallback, FormEvent } from "react";
import ReactMarkdown from "react-markdown";

/* ── Types ───────────────────────────────────────── */
interface Artifact {
  name: string;
  version: number;
  sessionId: string;
}

interface Message {
  id: string;
  role: "user" | "agent";
  text: string;
  tools?: string[];
  artifacts?: Artifact[];
}

interface AgentStep {
  agent: string;
  action: string;
  timestamp: number;
}

/* ── Config ──────────────────────────────────────── */
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
const APP_NAME = "wealth_pilot";
const USER_ID = "demo_user";

/* ── Component ───────────────────────────────────── */
export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [agentSteps, setAgentSteps] = useState<AgentStep[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  /* Create session on mount */
  const createSession = useCallback(async () => {
    try {
      const res = await fetch(
        `${API_URL}/apps/${APP_NAME}/users/${USER_ID}/sessions`,
        { method: "POST", headers: { "Content-Type": "application/json" } }
      );
      const data = await res.json();
      setSessionId(data.id);
      return data.id;
    } catch (err) {
      console.error("Failed to create session:", err);
      return null;
    }
  }, []);

  useEffect(() => {
    createSession();
  }, [createSession]);

  /* New chat */
  const handleNewChat = async () => {
    setMessages([]);
    setInput("");
    setAgentSteps([]);
    const id = await createSession();
    if (id) setSessionId(id);
  };

  /* Download artifact — opens the backend download endpoint directly */
  const handleDownload = (artifact: Artifact) => {
    const sid = artifact.sessionId;
    if (!sid) return;
    window.open(
      `${API_URL}/download/${APP_NAME}/${USER_ID}/${sid}/${artifact.name}`,
      "_blank"
    );
  };

  /* Derive a friendly action description */
  const describeAction = (agent: string, toolName?: string): string => {
    if (toolName) {
      const friendly: Record<string, string> = {
        fetch_stock_price: "Fetching stock data",
        allocate_portfolio: "Building portfolio",
        calculate_compound_growth: "Projecting growth",
        save_portfolio_report: "Generating report",
      };
      return friendly[toolName] || `Running ${toolName}`;
    }
    // No tool — the agent is thinking/responding
    const agentLabels: Record<string, string> = {
      WealthPilot: "Coordinating analysis",
      StockAnalyst: "Analyzing stock",
      PortfolioManager: "Managing portfolio",
      GrowthCalculator: "Calculating growth",
    };
    return agentLabels[agent] || "Thinking";
  };

  /* Send message */
  const handleSend = async (e?: FormEvent) => {
    e?.preventDefault();
    const text = input.trim();
    if (!text || isLoading) return;

    let sid = sessionId;
    if (!sid) {
      sid = await createSession();
      if (!sid) return;
    }

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      text,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);
    setAgentSteps([]);

    // Reset textarea height
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    try {
      const res = await fetch(`${API_URL}/run_sse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          app_name: APP_NAME,
          user_id: USER_ID,
          session_id: sid,
          streaming: false,
          new_message: {
            role: "user",
            parts: [{ text }],
          },
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const reader = res.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";
      let agentText = "";
      const toolCalls: string[] = [];
      const artifacts: Artifact[] = [];
      const agentMsgId = crypto.randomUUID();
      const steps: AgentStep[] = [];
      const seenAgents = new Set<string>();

      // Add placeholder agent message
      setMessages((prev) => [
        ...prev,
        { id: agentMsgId, role: "agent", text: "", tools: [], artifacts: [] },
      ]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const jsonStr = line.slice(6).trim();
          if (!jsonStr) continue;

          try {
            const event = JSON.parse(jsonStr);
            const author = event.author || "";

            // Track agent activity
            if (author && author !== "user") {
              let currentTool: string | undefined;

              // Extract text from content parts
              if (event.content?.parts) {
                for (const part of event.content.parts) {
                  if (part.text) {
                    agentText += part.text;
                  }
                    if (part.functionCall?.name) {
                    currentTool = part.functionCall.name;
                    if (currentTool && !toolCalls.includes(currentTool)) {
                      toolCalls.push(currentTool);
                    }
                  }
                  if (part.functionResponse?.name) {
                    const name = part.functionResponse.name;
                    if (!toolCalls.includes(name)) {
                      toolCalls.push(name);
                    }
                  }
                }
              }

              // Add step if this is a new agent or new tool call
              const action = describeAction(author, currentTool);
              const stepKey = `${author}:${currentTool || "think"}`;
              if (!seenAgents.has(stepKey)) {
                seenAgents.add(stepKey);
                steps.push({
                  agent: author,
                  action,
                  timestamp: Date.now(),
                });
                setAgentSteps([...steps]);
              }
            } else if (event.content?.parts) {
              // Events without author
              for (const part of event.content.parts) {
                if (part.text) agentText += part.text;
              }
            }

            // Detect artifacts from actions.artifactDelta
            if (event.actions?.artifactDelta) {
              for (const [name, versionId] of Object.entries(
                event.actions.artifactDelta
              )) {
                if (!artifacts.some((a) => a.name === name)) {
                  artifacts.push({
                    name,
                    version: versionId as number,
                    sessionId: sid!,
                  });
                }
              }
            }

            // Update the message incrementally
            setMessages((prev) =>
              prev.map((m) =>
                m.id === agentMsgId
                  ? {
                    ...m,
                    text: agentText,
                    tools: [...toolCalls],
                    artifacts: [...artifacts],
                  }
                  : m
              )
            );
          } catch {
            // Skip malformed events
          }
        }
      }

      // Final update
      if (!agentText.trim()) {
        agentText = "(Agent processed your request — check the results above)";
      }
      setMessages((prev) =>
        prev.map((m) =>
          m.id === agentMsgId
            ? {
              ...m,
              text: agentText,
              tools: [...toolCalls],
              artifacts: [...artifacts],
            }
            : m
        )
      );
    } catch (err) {
      console.error("Send error:", err);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "agent",
          text: "Sorry, something went wrong. Make sure the backend is running.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  /* Auto-resize textarea */
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 120) + "px";
  };

  /* Enter to send, Shift+Enter for newline */
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  /* Current active step (last one) */
  const activeStep = agentSteps.length > 0 ? agentSteps[agentSteps.length - 1] : null;

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <span className="logo">WealthPilot</span>
          <span className="badge">AI Advisor</span>
        </div>
        <button className="new-chat-btn" onClick={handleNewChat}>
          New Chat
        </button>
      </header>

      {/* Messages */}
      <div className="messages">
        {messages.length === 0 ? (
          <div className="empty-state">
            <h2>WealthPilot</h2>
            <p>
              Your AI Wealth Advisor. Ask about stocks, portfolios, and
              investment strategies.
            </p>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`message ${msg.role}`}>
              <span className="message-label">
                {msg.role === "user" ? "You" : "WealthPilot"}
              </span>
              {msg.tools && msg.tools.length > 0 && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                  {msg.tools.map((t) => (
                    <span key={t} className="tool-indicator">
                      <span
                        className={`tool-dot ${isLoading ? "active" : ""}`}
                      />
                      {t}
                    </span>
                  ))}
                </div>
              )}
              {msg.text ? (
                <div className="message-content">
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
                </div>
              ) : isLoading ? (
                <div className="typing">
                  <span />
                  <span />
                  <span />
                </div>
              ) : null}
              {/* Artifact download buttons */}
              {msg.artifacts && msg.artifacts.length > 0 && (
                <div className="artifact-list">
                  {msg.artifacts.map((a) => (
                    <button
                      key={a.name}
                      className="artifact-btn"
                      onClick={() => handleDownload(a)}
                    >
                      <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                        <polyline points="7 10 12 15 17 10" />
                        <line x1="12" y1="15" x2="12" y2="3" />
                      </svg>
                      {a.name}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="input-area">
        {/* Agent Progress — below divider, above input */}
        {agentSteps.length > 0 && (
          <div className={`agent-progress ${isLoading ? "" : "completed"}`}>
            <div className="progress-track">
              {agentSteps.map((step, i) => (
                <div
                  key={`${step.agent}-${step.action}`}
                  className={`progress-step ${isLoading && i === agentSteps.length - 1 ? "active" : "done"}`}
                >
                  <span className="step-dot" />
                  <span className="step-agent">{step.agent}</span>
                  <span className="step-action">{step.action}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        {isLoading && agentSteps.length === 0 && (
          <div className="agent-progress">
            <div className="progress-track">
              <div className="progress-step active">
                <span className="step-dot" />
                <span className="step-agent">WealthPilot</span>
                <span className="step-action">Starting</span>
              </div>
            </div>
          </div>
        )}
        <form className="input-wrapper" onSubmit={handleSend}>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Ask about stocks, portfolios, investments..."
            rows={1}
            disabled={isLoading}
          />
          <button
            type="submit"
            className="send-btn"
            disabled={!input.trim() || isLoading}
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M22 2L11 13" />
              <path d="M22 2L15 22L11 13L2 9L22 2Z" />
            </svg>
          </button>
        </form>
        <p className="footer-text">
          AI-generated analysis — not financial advice
        </p>
      </div>
    </div>
  );
}
