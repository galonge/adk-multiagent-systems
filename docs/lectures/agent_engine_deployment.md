# agent engine deployment — fully managed agents on vertex AI

> Agent Engine is Google Cloud's fully managed service for AI agents. deploy with one command,
> no Dockerfiles, no infrastructure — just your agent code.

---

## why Agent Engine

| feature | what it means |
|---|---|
| **fully managed** | no containers, no servers, no scaling config |
| **one-command deploy** | `adk deploy agent_engine` handles everything |
| **auto-scaling** | scales automatically based on demand |
| **built-in monitoring** | view agents in Cloud Console |
| **Vertex AI integration** | native access to Gemini models, no API key needed |

---

## Cloud Run vs Agent Engine

| | Cloud Run | Agent Engine |
|---|---|---|
| **infrastructure** | you manage containers | fully managed |
| **deployment** | Dockerfile + `gcloud` or `adk` CLI | `adk deploy agent_engine` |
| **scaling** | configurable (min/max instances) | automatic |
| **custom server logic** | ✅ full control (FastAPI) | ❌ managed runtime |
| **authentication** | API key or Vertex AI | Vertex AI (automatic) |
| **pricing** | pay per request/CPU/memory | pay per request ([pricing](https://cloud.google.com/vertex-ai/pricing#vertex-ai-agent-engine)) |
| **best for** | custom UIs, full control | fastest path to production |

---

## deploying to Agent Engine

### prerequisites

- GCP project with billing
- Vertex AI API enabled
- `gcloud` authenticated

### deploy command

```bash
export PROJECT_ID="my-wealth-pilot"
export LOCATION_ID="us-central1"

adk deploy agent_engine \
  --project=$PROJECT_ID \
  --region=$LOCATION_ID \
  --display_name="WealthPilot" \
  wealth_pilot
```

> ⏳ deployment takes several minutes — it packages your code, builds a container,
> and deploys to the managed runtime.

### deployment output

```
Deploying agent to Agent Engine...
✓ Code packaged
✓ Container built
✓ Agent deployed

Resource name: projects/my-wealth-pilot/locations/us-central1/reasoningEngines/751619551677906944
```

> 💡 save the **resource name** — you'll need the resource ID for testing.

---

## testing with Python SDK

```python
from vertexai import agent_engines

# connect to your deployed agent
remote_app = agent_engines.get("your-resource-name")

# create a session
session = await remote_app.async_create_session(user_id="demo_user")
print(f"Session ID: {session['id']}")

# send a query
async for event in remote_app.async_stream_query(
    user_id="demo_user",
    session_id=session["id"],
    message="analyze AAPL for me",
):
    print(event)
```

---

## testing with REST API

### find your resource ID

```bash
# from Cloud Console: Vertex AI → Agent Engine → API URLs → copy Query URL
# or via gcloud:
gcloud asset search-all-resources \
    --scope=projects/$PROJECT_ID \
    --asset-types='aiplatform.googleapis.com/ReasoningEngine' \
    --format="table(name,assetType,location)"
```

### set variables

```bash
export TOKEN=$(gcloud auth print-access-token)
export RESOURCE_ID="YOUR_RESOURCE_ID"
export AE_URL="https://${LOCATION_ID}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${LOCATION_ID}/reasoningEngines/${RESOURCE_ID}"
```

### check connection (GET — no `:query`)

```bash
curl -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "${AE_URL}"
```

### create a session

```bash
curl \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    "${AE_URL}:query" \
    -d '{"class_method": "async_create_session", "input": {"user_id": "u_123"}}'
```

> extract the `id` from the response — that's your session ID.

### send a query (streaming)

```bash
curl \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    "${AE_URL}:streamQuery?alt=sse" \
    -d '{
      "class_method": "async_stream_query",
      "input": {
        "user_id": "u_123",
        "session_id": "SESSION_ID_FROM_ABOVE",
        "message": "analyze AAPL"
      }
    }'
```

> ⚠️ **zsh users**: always use `${AE_URL}:query` (braces) — without braces, zsh
> interprets `$AE_URL:query` as a variable modifier and eats part of the URL.

---

## viewing in Cloud Console

navigate to: **Vertex AI → Agent Engine** in the [Cloud Console](https://console.cloud.google.com/vertex-ai/agents/agent-engines)

you'll see:
- your deployed agent with status, resource ID, and creation time
- ability to test interactively in the console

---

## cleanup

always clean up test deployments to avoid charges:

```bash
# via Python SDK
uv run --project wealth_pilot python -c "
import vertexai
client = vertexai.Client(project='$PROJECT_ID', location='$LOCATION_ID')
app = client.agent_engines.get(name='RESOURCE_NAME')
app.delete(force=True)
print('Deleted')
"

```

```bash
# or via REST API
export TOKEN=$(gcloud auth print-access-token)
curl -X DELETE \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/$PROJECT_ID/locations/$LOCATION_ID/reasoningEngines/RESOURCE_ID" \
  -H "Authorization: Bearer $TOKEN"
```

> ⚠️ `force=True` (Python) deletes child resources (sessions) too. use with care in production.

---

## docs & references

- [ADK Agent Engine Deployment](https://google.github.io/adk-docs/deploy/agent-engine/)
- [Standard Deployment Guide](https://google.github.io/adk-docs/deploy/agent-engine/deploy/)
- [Test Deployed Agents](https://google.github.io/adk-docs/deploy/agent-engine/test/)
- [Agent Engine Pricing](https://cloud.google.com/vertex-ai/pricing#vertex-ai-agent-engine)
