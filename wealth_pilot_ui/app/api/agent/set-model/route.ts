/**
 * set-model proxy — forwards model selection to Cloud Run.
 * POST /api/agent/set-model
 *
 * Proxies to the ADK Cloud Run /api/set-model endpoint.
 */

import { NextResponse } from "next/server";
import { getIdToken, CLOUD_RUN_BASE_URL } from "../auth";

export async function POST(request: Request) {
  try {
    const body = await request.json().catch(() => ({}));
    const token = await getIdToken();

    const res = await fetch(`${CLOUD_RUN_BASE_URL}/api/set-model`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      console.error("set-model failed:", res.status, await res.text());
      // acknowledge anyway to avoid frontend errors
      return NextResponse.json({
        status: "ok",
        model_id: body.model_id || "gemini-flash",
        message: "Model preference acknowledged (backend unreachable)",
      });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    console.error("set-model proxy error:", err);
    return NextResponse.json({
      status: "ok",
      model_id: "gemini-flash",
      message: "Model preference acknowledged (proxy error)",
    });
  }
}
