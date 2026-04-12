"""
WealthPilot V2 — model selector + scale-to-zero resilience.

activated only when ENABLE_WEALTHPILOT_V2=true.
provides:
  - multi-model registry (Gemini + Gemma 4)
  - per-request model switching via before_model_callback
  - Gemma endpoint health probing with TTL cache
  - /api/models and /api/set-model FastAPI endpoints
"""

import os
import time
import logging
from typing import Union
from pathlib import Path

# load .env early — ADK loads it lazily on first agent call, but we need
# GEMMA_ENDPOINT_URL and GEMMA_AUTH_TOKEN available for /api/models
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    from dotenv import load_dotenv

    load_dotenv(_env_file, override=False)

logger = logging.getLogger(__name__)

# ── feature flag ──────────────────────────────────
V2_ENABLED = os.getenv("ENABLE_WEALTHPILOT_V2", "").lower() == "true"

# ── per-session model preferences (in-memory) ────
# keyed by session_id → model_id string
_model_preferences: dict[str, str] = {}


# ── endpoint status cache ─────────────────────────
_gemma_status_cache = {
    "ready": None,  # True / False / None (unknown)
    "last_check": 0.0,
    "message": "",
}
_STATUS_CACHE_TTL = 30  # seconds


# ── auth helper ───────────────────────────────────


def _get_auth_token(endpoint_url: str) -> str:
    """get an auth token for the Gemma endpoint.

    priority chain:
    1. GEMMA_AUTH_TOKEN env var — for local testing with pre-obtained token
    2. ADC for Vertex AI — google.auth.default() → access token
    3. ADC for Cloud Run — google.oauth2.id_token → OIDC token
    4. fallback — gcloud auth print-identity-token
    """
    # 1. explicit token from env — for local dev or pre-rotated tokens
    explicit_token = os.getenv("GEMMA_AUTH_TOKEN")
    if explicit_token:
        logger.info("using explicit GEMMA_AUTH_TOKEN from env")
        return explicit_token

    # 2-4. ADC chain (works on Cloud Run with service account)
    import google.auth
    import google.auth.transport.requests

    auth_req = google.auth.transport.requests.Request()

    # Vertex AI endpoints → OAuth2 access token
    if "aiplatform.googleapis.com" in endpoint_url:
        credentials, _ = google.auth.default()
        credentials.refresh(auth_req)
        return credentials.token

    # Cloud Run endpoints → OIDC identity token
    try:
        from google.oauth2 import id_token as id_token_module

        return id_token_module.fetch_id_token(auth_req, endpoint_url)
    except Exception:
        import subprocess

        result = subprocess.run(
            ["gcloud", "auth", "print-identity-token"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        raise RuntimeError(
            "failed to get auth token. "
            "set GEMMA_AUTH_TOKEN env var or run 'gcloud auth application-default login'."
        )


# ── model creation ────────────────────────────────


def _create_gemma_model():
    """create a LiteLlm instance pointing at the Gemma 4 Vertex AI endpoint."""
    from google.adk.models.lite_llm import LiteLlm

    endpoint_url = os.getenv("GEMMA_ENDPOINT_URL", "")
    model_name = os.getenv("GEMMA_MODEL_NAME", "google/gemma-4-31B-it")
    token = _get_auth_token(endpoint_url)

    return LiteLlm(
        model=f"openai/{model_name}",
        base_url=f"{endpoint_url.rstrip('/')}/v1",
        num_retries=3,
        extra_body={
            "chat_template_kwargs": {"enable_thinking": True},
            "skip_special_tokens": False,
        },
        extra_headers={"Authorization": f"Bearer {token}"},
    )


def get_model_by_id(model_id: str) -> Union[str, object]:
    """resolve a UI-facing model ID to an ADK model."""
    if model_id == "gemini-pro":
        return "gemini-2.5-pro"
    elif model_id == "gemini-flash":
        return "gemini-2.5-flash"
    elif model_id == "gemma-4-31b":
        return _create_gemma_model()
    else:
        return "gemini-2.5-flash"  # safe fallback


# ── health probing ────────────────────────────────


def check_endpoint_ready() -> dict:
    """lightweight probe to check if the Gemma endpoint is responsive."""
    global _gemma_status_cache

    endpoint_url = os.getenv("GEMMA_ENDPOINT_URL")
    if not endpoint_url:
        return {
            "ready": False,
            "message": "Gemma endpoint not configured",
            "estimated_wait_seconds": None,
        }

    now = time.time()
    if (
        _gemma_status_cache["ready"] is not None
        and (now - _gemma_status_cache["last_check"]) < _STATUS_CACHE_TTL
    ):
        return {
            "ready": _gemma_status_cache["ready"],
            "message": _gemma_status_cache["message"],
            "estimated_wait_seconds": None if _gemma_status_cache["ready"] else 300,
        }

    try:
        import httpx

        token = _get_auth_token(endpoint_url)

        # vertex AI doesn't have /v1/models — use a lightweight chat probe
        if "aiplatform.googleapis.com" in endpoint_url:
            probe_url = f"{endpoint_url.rstrip('/')}/chat/completions"
            resp = httpx.post(
                probe_url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": os.getenv("GEMMA_MODEL_NAME", "gemma-4-31b-it"),
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 1,
                },
                timeout=15.0,
            )
        else:
            # Cloud Run / vLLM — /v1/models works
            probe_url = f"{endpoint_url.rstrip('/')}/v1/models"
            resp = httpx.get(
                probe_url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0,
            )

        if resp.status_code == 200:
            _gemma_status_cache.update(
                ready=True, last_check=now, message="model is ready"
            )
            return {
                "ready": True,
                "message": "model is ready",
                "estimated_wait_seconds": None,
            }

        if resp.status_code in (429, 404):
            # 429 = Cloud Run rate limit / cold start
            # 404 = Vertex AI scaled to zero
            msg = "model is scaling up from zero (~5-10 min)"
            _gemma_status_cache.update(ready=False, last_check=now, message=msg)
            return {"ready": False, "message": msg, "estimated_wait_seconds": 300}

        msg = f"unexpected status: {resp.status_code}"
        _gemma_status_cache.update(ready=False, last_check=now, message=msg)
        return {"ready": False, "message": msg, "estimated_wait_seconds": None}

    except Exception as e:
        msg = f"probe failed: {str(e)}"
        logger.warning(f"Gemma endpoint probe failed: {e}")
        _gemma_status_cache.update(ready=False, last_check=now, message=msg)
        return {"ready": False, "message": msg, "estimated_wait_seconds": None}


# ── model registry ────────────────────────────────


def get_available_models() -> dict:
    """return all available models with status info."""
    endpoint_url = os.getenv("GEMMA_ENDPOINT_URL")

    models = [
        {
            "id": "gemini-pro",
            "name": "Gemini 2.5 Pro",
            "status": "ready",
            "provider": "google",
            "description": "Deep reasoning and analysis",
        },
        {
            "id": "gemini-flash",
            "name": "Gemini 2.5 Flash",
            "status": "ready",
            "provider": "google",
            "description": "Fast and efficient",
        },
    ]

    # gemma always shows when V2 is enabled — status reflects availability
    if endpoint_url:
        probe = check_endpoint_ready()
        gemma_status = "ready" if probe["ready"] else "warming_up"
        models.append(
            {
                "id": "gemma-4-31b",
                "name": "Gemma 4 31B-it",
                "status": gemma_status,
                "provider": "self-hosted",
                "description": "Self-hosted open model on Vertex AI (H100)",
                "estimated_wait_seconds": probe.get("estimated_wait_seconds"),
                "status_message": probe["message"],
            }
        )
    else:
        # show Gemma as not configured but still visible
        models.append(
            {
                "id": "gemma-4-31b",
                "name": "Gemma 4 31B-it",
                "status": "not_configured",
                "provider": "self-hosted",
                "description": "Self-hosted open model (requires GEMMA_ENDPOINT_URL)",
                "estimated_wait_seconds": None,
                "status_message": "endpoint not configured",
            }
        )

    return {
        "models": models,
        "default_model": "gemini-flash",
        "gemma_configured": bool(endpoint_url),
    }


# ── ADK callbacks ─────────────────────────────────


def model_switcher_callback(callback_context, llm_request):
    """
    before_model_callback — reads model preference from in-memory store
    and swaps agent.model for this request.
    """
    session_id = callback_context.session.id
    pref = _model_preferences.get(session_id)

    if not pref:
        return None  # use default model

    agent = callback_context._invocation_context.agent
    new_model = get_model_by_id(pref)

    logger.info(f"switching {agent.name} to model: {pref}")
    agent.model = new_model

    return None  # proceed with the (now swapped) model


def on_model_error_callback(callback_context, llm_request, error):
    """
    on_model_error_callback — catches model errors and returns friendly messages.

    handles:
    - 429 / rate limit: Gemma cold-start (scale-to-zero)
    - 503 / UNAVAILABLE: Gemini overload — downgrades session to Flash
    """
    from google.genai.types import Content, Part
    from google.adk.models.llm_response import LlmResponse

    error_str = str(error).lower()
    session_id = callback_context.session.id
    agent = callback_context._invocation_context.agent

    # Gemma cold start (scale-to-zero)
    if "429" in error_str or "rate limit" in error_str or "not yet ready" in error_str:
        logger.warning(f"Gemma cold start detected: {error}")

        # invalidate the status cache so next poll reflects warming_up
        _gemma_status_cache["ready"] = False
        _gemma_status_cache["last_check"] = time.time()
        _gemma_status_cache["message"] = "model is scaling up from zero"

        return LlmResponse(
            content=Content(
                parts=[
                    Part(
                        text=(
                            "⏳ **Gemma 4 is currently warming up** (scale-to-zero cold start).\n\n"
                            "The model needs ~5-10 minutes to initialize on the GPU. "
                            "You can:\n"
                            "- **Switch to Gemini** using the model selector above for instant responses\n"
                            "- **Wait and retry** — the model is already scaling up from this request\n\n"
                            "I'll let you know when Gemma 4 is ready!"
                        )
                    )
                ]
            ),
        )

    # Gemini overload — downgrade this session to Flash and ask the user to retry
    if "503" in error_str or "unavailable" in error_str or "high demand" in error_str:
        logger.warning(
            f"Gemini overload on {agent.name} (session {session_id}): {error}. "
            "downgrading session to gemini-flash."
        )
        # update in-memory preference so next request uses Flash for this session
        _model_preferences[session_id] = "gemini-flash"
        agent.model = "gemini-2.5-flash"

        return LlmResponse(
            content=Content(
                parts=[
                    Part(
                        text=(
                            "⚡ **The selected model is experiencing high demand right now.**\n\n"
                            "I've automatically switched this session to **Gemini 2.5 Flash**. "
                            "Please resend your message and I'll respond right away.\n\n"
                            "*(You can also manually select a model using the selector above.)*"
                        )
                    )
                ]
            ),
        )

    return None  # let other errors propagate normally


# ── FastAPI endpoint registration ─────────────────


def register_v2_endpoints(app):
    """add /api/models and /api/set-model to the FastAPI app."""
    from pydantic import BaseModel

    class SetModelRequest(BaseModel):
        model_id: str
        session_id: str

    @app.get("/api/models")
    async def list_models():
        return get_available_models()

    @app.get("/api/models/{model_id}/status")
    async def model_status(model_id: str):
        if model_id == "gemma-4-31b":
            probe = check_endpoint_ready()
            return {
                "id": model_id,
                "status": "ready" if probe["ready"] else "warming_up",
                "message": probe["message"],
                "estimated_wait_seconds": probe.get("estimated_wait_seconds"),
            }
        return {"id": model_id, "status": "ready", "message": "always available"}

    @app.post("/api/set-model")
    async def set_model(req: SetModelRequest):
        _model_preferences[req.session_id] = req.model_id
        logger.info(f"model preference set: session={req.session_id} → {req.model_id}")
        return {"ok": True, "model_id": req.model_id}

    logger.info("V2 endpoints registered: /api/models, /api/set-model")


def patch_agent_callbacks(root_agent):
    """attach model_switcher and error callbacks to all LLM agents in the tree."""
    from google.adk.agents import LlmAgent

    def _patch(agent):
        if isinstance(agent, LlmAgent):
            # add before_model_callback
            existing = agent.before_model_callback
            if existing is None:
                agent.before_model_callback = model_switcher_callback
            elif isinstance(existing, list):
                existing.insert(0, model_switcher_callback)
            else:
                agent.before_model_callback = [model_switcher_callback, existing]

            # add on_model_error_callback
            existing_err = agent.on_model_error_callback
            if existing_err is None:
                agent.on_model_error_callback = on_model_error_callback
            elif isinstance(existing_err, list):
                existing_err.insert(0, on_model_error_callback)
            else:
                agent.on_model_error_callback = [on_model_error_callback, existing_err]

            logger.info(f"V2 callbacks patched on: {agent.name}")

        # recurse into sub-agents
        if hasattr(agent, "sub_agents"):
            for sub in agent.sub_agents:
                _patch(sub)

    _patch(root_agent)
    logger.info("all agents patched with V2 model switching callbacks")
