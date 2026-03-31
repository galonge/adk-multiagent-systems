# google cloud prerequisites — setting up for production deployment

> before deploying your ADK agents to Cloud Run or Agent Engine, you need a Google Cloud
> project with the right APIs enabled and authentication configured.

---

## what you'll need

| requirement | what it is | how to get it |
|---|---|---|
| GCP account | access to Google Cloud | [console.cloud.google.com](https://console.cloud.google.com) |
| project | container for your resources | create on [project page](https://console.cloud.google.com/projectcreate) |
| billing | pay-as-you-go or free trial | [billing page](https://console.cloud.google.com/billing) |
| `gcloud` CLI | command-line access to GCP | [install guide](https://cloud.google.com/sdk/docs/install) |

> 💡 **free trial**: new users get $300 in credits for 90 days — more than enough
> to test agent deployments.

---

## step-by-step setup

### 1. create or select a project

```bash
# create a new project
gcloud projects create my-wealth-pilot --name="WealthPilot"

# or set an existing project
gcloud config set project my-wealth-pilot
```

### 2. get your project ID

```bash
gcloud config get-value project
# → my-wealth-pilot
```

> ⚠️ use the **project ID** (alphanumeric with hyphens), not the project number.

### 3. enable billing

link a billing account at [console.cloud.google.com/billing](https://console.cloud.google.com/billing).

### 4. authenticate

```bash
# login to gcloud
gcloud auth login

# set application default credentials (for Python SDK)
gcloud auth application-default login
```

### 5. enable required APIs

```bash
# vertex AI (required for Agent Engine + Gemini models)
gcloud services enable aiplatform.googleapis.com

# cloud run (required for Cloud Run deployment)
gcloud services enable run.googleapis.com

# artifact registry (required for container images)
gcloud services enable artifactregistry.googleapis.com

# cloud build (used by adk deploy)
gcloud services enable cloudbuild.googleapis.com

# secret manager (required for Cloud Run deployment)
gcloud services enable secretmanager.googleapis.com
```

### 6. grant IAM permissions for Cloud Build

Cloud Build uses the default Compute Engine service account. It needs permission to
write logs and push container images:

```bash
# get your project number
export PROJECT_NUMBER=$(gcloud projects describe $GOOGLE_CLOUD_PROJECT --format="value(projectNumber)")

# grant Logs Writer (required for build logs)
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/logging.logWriter" --quiet

# grant Artifact Registry Writer (required to push container images)
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/artifactregistry.writer" --quiet
```

> ⚠️ without these roles, `adk deploy cloud_run` will fail silently during the image push
> step — the Docker build succeeds but the deploy reports "Build failed" with no logs.

### 7. set environment variables

```bash
export GOOGLE_CLOUD_PROJECT="my-wealth-pilot"
export GOOGLE_CLOUD_LOCATION="us-central1"
```

### 8. store your API key in Secret Manager

```bash
# create the secret
echo -n "YOUR_GOOGLE_API_KEY" | \
  gcloud secrets create google-api-key --data-file=-

# grant Cloud Run access to the secret
gcloud secrets add-iam-policy-binding google-api-key \
  --member="serviceAccount:$(gcloud iam service-accounts list --format='value(email)' --filter='compute')" \
  --role="roles/secretmanager.secretAccessor"

# grant storage access to GCS 
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="serviceAccount:$(gcloud iam service-accounts list --format='value(email)' --filter='compute')" \
  --role="roles/storage.objectViewer"
```

---

## what each deployment option needs

| requirement | Cloud Run | Agent Engine |
|---|---|---|
| GCP project | ✅ | ✅ |
| billing enabled | ✅ | ✅ |
| Vertex AI API | optional (can use API key) | ✅ required |
| Cloud Run API | ✅ required | ❌ |
| Artifact Registry API | ✅ required | ❌ (handled for you) |
| Cloud Build API | ✅ required | ❌ (handled for you) |
| `gcloud` CLI | ✅ | ✅ |
| Secret Manager | recommended | ❌ (uses Vertex AI auth) |

---

## docs & references

- [Google Cloud Console](https://console.cloud.google.com)
- [gcloud CLI Installation](https://cloud.google.com/sdk/docs/install)
- [Enable APIs](https://console.cloud.google.com/apis/library)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)
