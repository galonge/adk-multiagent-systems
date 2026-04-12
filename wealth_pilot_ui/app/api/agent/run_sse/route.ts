/**
 * streaming query proxy — forwards SSE from Cloud Run ADK server.
 * POST /api/agent/run_sse
 *
 * ADK Cloud Run endpoint:
 *   POST {CLOUD_RUN_URL}/run_sse
 *
 * The ADK server returns native SSE events in the format:
 *   data: {"author": "...", "content": {...}, ...}\n\n
 *
 * This proxy forwards the stream directly — no translation needed.
 */

import { getIdToken, CLOUD_RUN_BASE_URL } from "../auth";

export const maxDuration = 60;

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const {
      app_name = "wealth_pilot",
      user_id = "demo_user",
      session_id,
      new_message,
      streaming = false,
    } = body;

    if (!session_id || !new_message) {
      return new Response(
        JSON.stringify({ error: "session_id and new_message are required" }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    const token = await getIdToken();

    // Forward the full request body to the ADK Cloud Run /run_sse endpoint.
    const res = await fetch(`${CLOUD_RUN_BASE_URL}/run_sse`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ app_name, user_id, session_id, new_message, streaming }),
    });

    if (!res.ok) {
      const error = await res.text();
      console.error("cloud run run_sse failed:", error);
      return new Response(
        JSON.stringify({ error: "stream query failed", detail: error }),
        { status: res.status, headers: { "Content-Type": "application/json" } }
      );
    }

    // Pipe the SSE stream directly through — ADK format is already correct.
    return new Response(res.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  } catch (err) {
    console.error("run_sse proxy error:", err);
    return new Response(
      JSON.stringify({ error: "internal proxy error" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
}
