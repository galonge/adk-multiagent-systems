/**
 * session creation proxy — creates a new ADK session on Cloud Run.
 * POST /api/agent/sessions
 *
 * ADK Cloud Run endpoint:
 *   POST {CLOUD_RUN_URL}/apps/{app}/users/{user}/sessions
 */

import { NextResponse } from "next/server";
import { getIdToken, CLOUD_RUN_BASE_URL, ADK_APP_NAME } from "../auth";

export async function POST(request: Request) {
  try {
    const body = await request.json().catch(() => ({}));
    const userId = body.user_id || "demo_user";

    const token = await getIdToken();

    const url = `${CLOUD_RUN_BASE_URL}/apps/${ADK_APP_NAME}/users/${userId}/sessions`;

    const res = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({}),
    });

    if (!res.ok) {
      const error = await res.text();
      console.error("session creation failed:", error);
      return NextResponse.json(
        { error: "failed to create session" },
        { status: res.status }
      );
    }

    const session = await res.json();
    return NextResponse.json(session);
  } catch (err) {
    console.error("session proxy error:", err);
    return NextResponse.json(
      { error: "internal proxy error" },
      { status: 500 }
    );
  }
}
