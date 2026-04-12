/**
 * models proxy — returns available models from Cloud Run.
 * GET /api/agent/models
 *
 * Proxies to the ADK Cloud Run /api/models endpoint which
 * returns the available models based on backend configuration.
 */

import { NextResponse } from "next/server";
import { getIdToken, CLOUD_RUN_BASE_URL } from "../auth";

export async function GET() {
  try {
    const token = await getIdToken();

    const res = await fetch(`${CLOUD_RUN_BASE_URL}/api/models`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) {
      console.error("models fetch failed:", res.status, await res.text());
      // fallback to a sensible default if backend is unreachable
      return NextResponse.json({
        models: [
          {
            id: "gemini-flash",
            name: "Gemini 2.5 Flash",
            status: "ready",
            provider: "google",
            description: "Fast and efficient",
          },
        ],
        default_model: "gemini-flash",
        gemma_configured: false,
      });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    console.error("models proxy error:", err);
    // graceful fallback
    return NextResponse.json({
      models: [
        {
          id: "gemini-flash",
          name: "Gemini 2.5 Flash",
          status: "ready",
          provider: "google",
          description: "Fast and efficient",
        },
      ],
      default_model: "gemini-flash",
      gemma_configured: false,
    });
  }
}
