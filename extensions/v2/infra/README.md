# WealthPilot V2 — infrastructure

Pulumi YAML project that provisions all GCP resources needed for the WealthPilot V2
production deployment on Cloud Run with Vercel frontend.

## what gets created

| resource | purpose |
|----------|---------|
| WIF identity pool (`vercel`) | OIDC trust relationship with Vercel |
| WIF OIDC provider (`vercel`) | maps Vercel-issued tokens to GCP identities |
| service account (`vercel-wealthpilot`) | Vercel proxy identity for Cloud Run calls |
| GCS bucket (`{project}-wealthpilot-artifacts`) | persistent storage for PDF report artifacts |
| IAM: `roles/run.invoker` | SA can call the Cloud Run service |
| IAM: `roles/iam.serviceAccountTokenCreator` | SA can generate ID tokens for itself (required for Cloud Run auth) |
| IAM: `roles/iam.workloadIdentityUser` | WIF can impersonate SA |
| IAM: `roles/storage.objectAdmin` | SA and Cloud Run compute SA can read/write artifact bucket |
| IAM: `roles/aiplatform.user` | SA can call Vertex AI APIs (model inference, if needed) |
| API enablement | `aiplatform`, `iam`, `storage`, `sts`, `iamcredentials`, `run` |

## prerequisites

1. **Pulumi CLI** installed: `brew install pulumi`
2. **GCP CLI** authenticated: `gcloud auth application-default login`
3. **Pulumi GCS backend** (already configured for this project):

```bash
# this bucket already exists from the gemma4 extension
gsutil mb gs://<YOUR_GCP_PROJECT_ID>-pulumi-state
gsutil versioning set on gs://<YOUR_GCP_PROJECT_ID>-pulumi-state
```

## secrets & passphrase

Pulumi encrypts config secrets using a passphrase. we store it in a gitignored `.passphrase` file
so you don't have to type it every time.

```bash
# create the passphrase file (one-time setup)
cp .passphrase.example .passphrase

# edit it — put your actual passphrase on a single line
# this is the passphrase you used during 'pulumi stack init dev'
```

every Pulumi command then uses the file via the `PULUMI_CONFIG_PASSPHRASE_FILE` env var:

```bash
export PULUMI_CONFIG_PASSPHRASE_FILE=.passphrase
```

> `.passphrase` is gitignored. never commit it.

## usage

```bash
cd extensions/v2/infra

# set the passphrase file (once per terminal session)
export PULUMI_CONFIG_PASSPHRASE_FILE=.passphrase

# initialize the stack (first time only)
pulumi login gs://<YOUR_GCP_PROJECT_ID>-pulumi-state
pulumi stack init dev

# preview what will be created — always do this first
pulumi preview

# provision all resources
pulumi up

# view outputs (SA email, bucket name, WIF IDs)
pulumi stack output

# tear down everything
pulumi destroy
```

## after provisioning

once `pulumi up` completes:

1. **deploy the agent** to Cloud Run:

```bash
export GOOGLE_CLOUD_PROJECT="<YOUR_GCP_PROJECT_ID>"
export GOOGLE_CLOUD_LOCATION="us-central1"

adk deploy cloud_run \
  --project=$GOOGLE_CLOUD_PROJECT \
  --region=$GOOGLE_CLOUD_LOCATION \
  --service_name=wealth-pilot-service \
  wealth_pilot
```

note the Cloud Run service URL from the output (e.g. `https://wealth-pilot-service-xxxx-uc.a.run.app`).

2. **set Vercel env vars** using the Pulumi outputs:

```bash
cd wealth_pilot_ui

# use printf (not echo) to avoid embedding a trailing newline in env var values.
# a trailing newline in CLOUD_RUN_URL will break ID token auth (aud mismatch → 401).
printf "<YOUR_GCP_PROJECT_ID>"               | vercel env add GCP_PROJECT_ID production
printf "<YOUR_GCP_PROJECT_NUMBER>"           | vercel env add GCP_PROJECT_NUMBER production
printf "$(pulumi -C extensions/v2/infra stack output serviceAccountEmail)" \
                                                     | vercel env add GCP_SERVICE_ACCOUNT_EMAIL production
printf "vercel"                                      | vercel env add GCP_WORKLOAD_IDENTITY_POOL_ID production
printf "vercel"                                      | vercel env add GCP_WORKLOAD_IDENTITY_POOL_PROVIDER_ID production
printf "https://wealth-pilot-service-xxxx-uc.a.run.app" \
                                                     | vercel env add CLOUD_RUN_URL production
printf "wealth_pilot"                                | vercel env add ADK_APP_NAME production
printf "$(pulumi -C extensions/v2/infra stack output artifactsBucket)" \
                                                     | vercel env add GCP_ARTIFACTS_BUCKET production
```

3. **enable OIDC** in Vercel Dashboard → Settings → Security → Secure backend access

4. **deploy frontend**: `vercel --prod`

## stack configuration

`Pulumi.dev.yaml` is gitignored. create it from the example before running any Pulumi commands:

```bash
cp Pulumi.dev.yaml.example Pulumi.dev.yaml
# edit Pulumi.dev.yaml and fill in your values
```

values to set:
- `project` — GCP project ID
- `region` — GCP region
- `project-number` — GCP project number (used for WIF audience)
- `vercel-team` — Vercel team slug
- `vercel-project` — Vercel project name (must match exactly)
- `cloud-run-service` — Cloud Run service name (must match `--service_name` from deploy)

## troubleshooting

### IAM propagation delay

after `pulumi up`, IAM changes take **1–2 minutes** to propagate globally. if you see
403 errors from `iamcredentials.googleapis.com/generateIdToken` immediately after
provisioning, wait a moment and retry.

### CLOUD_RUN_URL has a trailing newline

symptom: Cloud Run returns 401 even though the ID token generates successfully.

diagnosis: decode the ID token JWT payload (base64 decode the middle segment) and
check the `aud` claim. if it ends with `\n`, the env var was set using `echo`.

fix:
```bash
vercel env rm CLOUD_RUN_URL production --yes
printf "https://your-service.run.app" | vercel env add CLOUD_RUN_URL production
vercel --prod
```

### generateIdToken returns 403

the SA is missing `roles/iam.serviceAccountTokenCreator`. check the Pulumi stack includes
the `sa-token-creator` binding and that `pulumi up` completed without errors. wait 1–2
minutes for IAM propagation, then retry.

## notes

- the WIF pool and provider are project-level resources — they can be shared with other
  Vercel projects if needed (add additional SA + IAM bindings per project)
- the GCS artifacts bucket uses `uniformBucketLevelAccess` and `publicAccessPrevention: enforced` —
  all access goes through IAM, no public URLs
- the Vercel OIDC issuer uses the team-scoped URL (`https://oidc.vercel.com/<YOUR_VERCEL_TEAM>`) for
  tighter security — only this team's deployments can authenticate
