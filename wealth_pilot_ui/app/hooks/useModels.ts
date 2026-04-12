"use client";

import { useState, useEffect, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";
const useProxy = !API_URL;

export interface Model {
  id: string;
  name: string;
  status: "ready" | "warming_up" | "not_configured";
  provider: string;
  description: string;
  estimated_wait_seconds?: number | null;
  status_message?: string;
}

interface ModelsResponse {
  models: Model[];
  default_model: string;
  gemma_configured: boolean;
}

interface UseModelsReturn {
  models: Model[];
  selectedModel: Model | null;
  selectModel: (modelId: string, sessionId: string | null) => Promise<void>;
  gemmaStatus: "ready" | "warming_up" | "not_configured" | null;
  gemmaJustBecameReady: boolean;
  clearGemmaReadyFlag: () => void;
  isLoading: boolean;
}

const FALLBACK_MODELS: Model[] = [
  {
    id: "gemini-pro",
    name: "Gemini 2.5 Pro",
    status: "ready",
    provider: "google",
    description: "Deep reasoning and analysis",
  },
  {
    id: "gemini-flash",
    name: "Gemini 2.5 Flash",
    status: "ready",
    provider: "google",
    description: "Fast and efficient",
  },
  {
    id: "gemma-4-31b",
    name: "Gemma 4 31B-it",
    status: "not_configured",
    provider: "self-hosted",
    description: "Self-hosted open model (requires GEMMA_ENDPOINT_URL)",
  },
];

export function useModels(): UseModelsReturn {
  const [models, setModels] = useState<Model[]>(FALLBACK_MODELS);
  const [selectedId, setSelectedId] = useState<string>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("wp_model") || "gemini-flash";
    }
    return "gemini-flash";
  });
  const [gemmaJustBecameReady, setGemmaJustBecameReady] = useState(false);
  const [prevGemmaStatus, setPrevGemmaStatus] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // fetch models from backend
  const fetchModels = useCallback(async () => {
    try {
      const url = useProxy
        ? "/api/agent/models"
        : `${API_URL}/api/models`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: ModelsResponse = await res.json();
      setModels(data.models);

      // detect warming_up → ready transition for toast
      const gemma = data.models.find((m) => m.id === "gemma-4-31b");
      if (gemma) {
        if (prevGemmaStatus === "warming_up" && gemma.status === "ready") {
          setGemmaJustBecameReady(true);
        }
        setPrevGemmaStatus(gemma.status);
      }
    } catch {
      // backend might not have /api/models — use fallbacks
      setModels(FALLBACK_MODELS);
    } finally {
      setIsLoading(false);
    }
  }, [prevGemmaStatus]);

  // initial fetch + polling every 45s
  useEffect(() => {
    fetchModels();
    const interval = setInterval(fetchModels, 45_000);
    return () => clearInterval(interval);
  }, [fetchModels]);

  // select model
  const selectModel = useCallback(
    async (modelId: string, sessionId: string | null) => {
      setSelectedId(modelId);
      localStorage.setItem("wp_model", modelId);

      // tell backend to switch model for this session
      if (sessionId) {
        try {
          const url = useProxy
            ? "/api/agent/set-model"
            : `${API_URL}/api/set-model`;
          await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ model_id: modelId, session_id: sessionId }),
          });
        } catch {
          // best-effort — don't block UI
        }
      }
    },
    [],
  );

  const selectedModel = models.find((m) => m.id === selectedId) || models[0];
  const gemma = models.find((m) => m.id === "gemma-4-31b");

  return {
    models,
    selectedModel,
    selectModel,
    gemmaStatus: gemma?.status || null,
    gemmaJustBecameReady,
    clearGemmaReadyFlag: () => setGemmaJustBecameReady(false),
    isLoading,
  };
}
