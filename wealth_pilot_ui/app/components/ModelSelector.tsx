"use client";

import { useState, useRef, useEffect } from "react";
import { Model } from "../hooks/useModels";

interface ModelSelectorProps {
  models: Model[];
  selectedModel: Model | null;
  onSelect: (modelId: string) => void;
}

export function ModelSelector({
  models,
  selectedModel,
  onSelect,
}: ModelSelectorProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const statusColor = (status: string) => {
    if (status === "ready") return "#4ade80";
    if (status === "warming_up") return "#eab308";
    return "#666";
  };

  const statusLabel = (status: string) => {
    if (status === "ready") return "Ready";
    if (status === "warming_up") return "Warming up";
    return "Offline";
  };

  return (
    <div className="model-selector" ref={ref}>
      <button
        className="model-selector-btn"
        onClick={() => setOpen(!open)}
        type="button"
        id="model-selector-toggle"
      >
        <span
          className="model-dot"
          style={{ background: statusColor(selectedModel?.status || "ready") }}
        />
        <span className="model-name">{selectedModel?.name || "Model"}</span>
        <svg
          width="10"
          height="10"
          viewBox="0 0 10 10"
          fill="currentColor"
          style={{
            transform: open ? "rotate(180deg)" : "none",
            transition: "transform 0.15s ease",
          }}
        >
          <path d="M2 3.5L5 6.5L8 3.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
        </svg>
      </button>

      {open && (
        <div className="model-dropdown">
          {models.map((m) => (
            <button
              key={m.id}
              className={`model-option ${m.id === selectedModel?.id ? "active" : ""}`}
              onClick={() => {
                if (m.status !== "not_configured") {
                  onSelect(m.id);
                  setOpen(false);
                }
              }}
              disabled={m.status === "not_configured"}
              type="button"
              id={`model-option-${m.id}`}
            >
              <div className="model-option-left">
                <span
                  className="model-dot"
                  style={{ background: statusColor(m.status) }}
                />
                <div>
                  <div className="model-option-name">{m.name}</div>
                  <div className="model-option-desc">{m.description}</div>
                </div>
              </div>
              <span
                className={`model-status-badge ${m.status}`}
              >
                {statusLabel(m.status)}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
