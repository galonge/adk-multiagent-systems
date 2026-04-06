"""
WealthPilot — Production FastAPI Server
Uses ADK's get_fast_api_app() for a production-ready deployment.
"""

import os
import base64
import uvicorn
from fastapi import HTTPException
from fastapi.responses import Response

from google.adk.cli.fast_api import get_fast_api_app
import logging

# import agentops
# agentops.init(
#     api_key=os.getenv("AGENT_OPS_API_KEY"),
# )

# AGENT_DIR must be the PARENT directory that CONTAINS agent folders.
# get_fast_api_app scans subdirectories looking for agent.py files.
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# If we're inside the agent directory itself (has agent.py next to main.py),
# move up one level so get_fast_api_app can discover it as a subdirectory.
if os.path.exists(os.path.join(AGENT_DIR, "agent.py")):
    subdir = os.path.join(AGENT_DIR, "wealth_pilot")
    if not os.path.exists(os.path.join(subdir, "agent.py")):
        AGENT_DIR = os.path.dirname(AGENT_DIR)

# Allow all origins for the custom frontend
ALLOWED_ORIGINS = ["*"]

logging.basicConfig(
   level=logging.INFO,
   format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

# Create the FastAPI app using ADK's helper
# web=False — we don't need the Dev UI in production
app = get_fast_api_app(
    agents_dir=AGENT_DIR,
    allow_origins=ALLOWED_ORIGINS,
    web=False,
)


# Custom endpoint to serve artifacts (PDFs) for inline browser preview
@app.get("/download/{app_name}/{user_id}/{session_id}/{artifact_name}")
async def download_artifact(
    app_name: str, user_id: str, session_id: str, artifact_name: str
):
    """Serve an artifact as inline content so the browser displays it."""
    import httpx

    port = os.environ.get("PORT", 8080)
    url = f"http://127.0.0.1:{port}/apps/{app_name}/users/{user_id}/sessions/{session_id}/artifacts/{artifact_name}"

    async with httpx.AsyncClient() as client:
        res = await client.get(url)

    if res.status_code != 200:
        raise HTTPException(status_code=404, detail="Artifact not found")

    data = res.json()
    inline_data = data.get("inlineData", data.get("inline_data", {}))
    b64 = inline_data.get("data", "")
    mime_type = inline_data.get("mimeType", "application/pdf")

    if not b64:
        raise HTTPException(status_code=404, detail="No artifact data")

    padding = 4 - len(b64) % 4
    if padding != 4:
        b64 += "=" * padding
    raw_bytes = base64.urlsafe_b64decode(b64)

    filename = artifact_name if "." in artifact_name else f"{artifact_name}.pdf"

    return Response(
        content=raw_bytes,
        media_type=mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Access-Control-Allow-Origin": "*",
        },
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)