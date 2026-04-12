"""
WealthPilot — production FastAPI server.
uses ADK's get_fast_api_app() for a production-ready deployment.

V2 features (model selector, theme toggle, Gemma 4 support) are
activated by ENABLE_WEALTHPILOT_V2=true.
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

# AGENT_DIR is the directory containing main.py.
# get_fast_api_app scans its subdirectories looking for agent.py files.
# In Docker, the Dockerfile places agent code in /app/wealth_pilot/
# Locally, the parent directory (multi-agent-systems/) contains wealth_pilot/
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# If agent.py is alongside main.py (flat structure for local dev),
# we need the PARENT directory so get_fast_api_app can find "wealth_pilot/"
# as a subdirectory containing agent.py
if os.path.exists(os.path.join(AGENT_DIR, "agent.py")) and not os.path.exists(
    os.path.join(AGENT_DIR, "wealth_pilot", "agent.py")
):
    # flat structure (local dev when running from wealth_pilot/)
    # go up one level so get_fast_api_app finds wealth_pilot/ as a subdir
    AGENT_DIR = os.path.dirname(AGENT_DIR)

# allow all origins for the custom frontend
ALLOWED_ORIGINS = ["*"]

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

# create the FastAPI app using ADK's helper
# web=False — we don't need the Dev UI in production
# when ARTIFACTS_BUCKET is set, use GCS for persistent artifact storage (PDFs);
# otherwise fall back to InMemory for local development.
ARTIFACTS_BUCKET = os.getenv("ARTIFACTS_BUCKET")

app_kwargs = dict(
    agents_dir=AGENT_DIR,
    allow_origins=ALLOWED_ORIGINS,
    web=False,
)
if ARTIFACTS_BUCKET:
    app_kwargs["artifact_service_uri"] = f"gs://{ARTIFACTS_BUCKET}"
    logging.info(f"Using GCS artifact storage: gs://{ARTIFACTS_BUCKET}")
else:
    logging.info("Using in-memory artifact storage (local dev)")

app = get_fast_api_app(**app_kwargs)

# ── V2: model selector + Gemma 4 support ─────────
# activated by ENABLE_WEALTHPILOT_V2=true
V2_ENABLED = os.getenv("ENABLE_WEALTHPILOT_V2", "").lower() == "true"

if V2_ENABLED:
    try:
        from .v2 import register_v2_endpoints, patch_agent_callbacks
    except ImportError:
        from v2 import register_v2_endpoints, patch_agent_callbacks
    register_v2_endpoints(app)
    logging.info("WealthPilot V2 enabled — model selector + Gemma 4 support active")

    # patch agent callbacks on first request (agent tree isn't loaded until then)
    _v2_agents_patched = False

    @app.middleware("http")
    async def v2_patch_middleware(request, call_next):
        global _v2_agents_patched
        if not _v2_agents_patched:
            try:
                import importlib

                mod = importlib.import_module("wealth_pilot.agent")
                patch_agent_callbacks(mod.root_agent)
                _v2_agents_patched = True
            except Exception as e:
                logging.warning(f"V2 agent patch deferred: {e}")
        return await call_next(request)


# custom endpoint to serve artifacts (PDFs) for inline browser preview
@app.get("/download/{app_name}/{user_id}/{session_id}/{artifact_name}")
async def download_artifact(
    app_name: str, user_id: str, session_id: str, artifact_name: str
):
    """serve an artifact as inline content so the browser displays it."""
    import httpx

    port = os.environ.get("PORT", 8000)
    base = os.environ.get("BASE_URL", f"http://localhost:{port}")
    url = f"{base}/apps/{app_name}/users/{user_id}/sessions/{session_id}/artifacts/{artifact_name}"

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
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
