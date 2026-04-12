/**
 * artifact download proxy — fetches artifacts from Cloud Run.
 * GET /api/agent/artifacts?filename=...&session_id=...&user_id=...
 *
 * Proxies to the ADK Cloud Run download endpoint which returns
 * the artifact binary (PDF, etc.) for inline browser display.
 */

import { NextResponse } from "next/server";
import { getIdToken, CLOUD_RUN_BASE_URL, ADK_APP_NAME } from "../auth";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const filename = searchParams.get("filename");
    const sessionId = searchParams.get("session_id");
    const userId = searchParams.get("user_id") || "demo_user";

    if (!filename || !sessionId) {
      return NextResponse.json(
        { error: "filename and session_id are required" },
        { status: 400 }
      );
    }

    const token = await getIdToken();

    // Call the Cloud Run download endpoint (defined in wealth_pilot/main.py)
    const url = `${CLOUD_RUN_BASE_URL}/download/${ADK_APP_NAME}/${userId}/${sessionId}/${filename}`;

    const res = await fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) {
      const error = await res.text();
      console.error("artifact download failed:", error);
      return NextResponse.json(
        { error: "failed to download artifact" },
        { status: res.status }
      );
    }

    // Pipe the binary response through with the correct headers
    const contentType = res.headers.get("content-type") || "application/octet-stream";
    const contentDisposition = res.headers.get("content-disposition") || `inline; filename="${filename}"`;

    return new Response(res.body, {
      headers: {
        "Content-Type": contentType,
        "Content-Disposition": contentDisposition,
      },
    });
  } catch (err) {
    console.error("artifact proxy error:", err);
    return NextResponse.json(
      { error: "internal proxy error" },
      { status: 500 }
    );
  }
}
