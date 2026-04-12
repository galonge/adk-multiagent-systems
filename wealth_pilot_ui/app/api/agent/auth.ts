/**
 * shared auth & config — gets a GCP ID token to call Cloud Run.
 *
 * Cloud Run requires an ID token (not an access token), with the
 * audience set to the Cloud Run service URL.
 *
 * In production (Vercel): Vercel OIDC → WIF → SA impersonation → ID token
 * In development: uses GCP_ACCESS_TOKEN env var directly (gcloud print-access-token)
 *
 * Reference: https://vercel.com/docs/oidc/gcp
 */

import { ExternalAccountClient } from "google-auth-library";

// Cloud Run base URL — all ADK endpoints live here
export const CLOUD_RUN_BASE_URL = process.env.CLOUD_RUN_URL!;

// ADK app name — used in session URL paths
export const ADK_APP_NAME = process.env.ADK_APP_NAME || "wealth_pilot";

/**
 * Get a GCP ID token for calling the Cloud Run service.
 * Falls back to a raw access token in development (works for most calls).
 */
export async function getIdToken(): Promise<string> {
  // development fallback — use a pre-obtained gcloud token
  if (process.env.GCP_ACCESS_TOKEN) {
    return process.env.GCP_ACCESS_TOKEN;
  }

  // production — Vercel OIDC → GCP WIF → service account → ID token
  const { getVercelOidcToken } = await import("@vercel/oidc");

  const projectNumber = process.env.GCP_PROJECT_NUMBER!;
  const poolId = process.env.GCP_WORKLOAD_IDENTITY_POOL_ID || "vercel";
  const providerId = process.env.GCP_WORKLOAD_IDENTITY_POOL_PROVIDER_ID || "vercel";
  const serviceAccountEmail = process.env.GCP_SERVICE_ACCOUNT_EMAIL!;
  const audience = CLOUD_RUN_BASE_URL; // Cloud Run ID token audience = service URL

  console.log("[auth] CLOUD_RUN_BASE_URL:", CLOUD_RUN_BASE_URL);
  console.log("[auth] audience for ID token:", audience);
  console.log("[auth] serviceAccountEmail:", serviceAccountEmail);
  console.log("[auth] projectNumber:", projectNumber);

  // Step 1: exchange Vercel OIDC token for a GCP access token via WIF
  const authClient = ExternalAccountClient.fromJSON({
    type: "external_account",
    audience: `//iam.googleapis.com/projects/${projectNumber}/locations/global/workloadIdentityPools/${poolId}/providers/${providerId}`,
    subject_token_type: "urn:ietf:params:oauth:token-type:jwt",
    token_url: "https://sts.googleapis.com/v1/token",
    service_account_impersonation_url: `https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/${serviceAccountEmail}:generateAccessToken`,
    subject_token_supplier: {
      getSubjectToken: async () => getVercelOidcToken(),
    },
  });

  if (!authClient) {
    throw new Error("failed to create ExternalAccountClient");
  }

  // Step 2: use the access token to generate an ID token for the Cloud Run audience
  const accessTokenResponse = await authClient.getAccessToken();
  if (!accessTokenResponse.token) {
    throw new Error("failed to obtain GCP access token via WIF");
  }
  console.log("[auth] Step 2 OK: got access token (length:", accessTokenResponse.token.length, ")");

  // Step 3: generateIdToken from the SA
  const genUrl = `https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/${serviceAccountEmail}:generateIdToken`;
  console.log("[auth] Step 3: calling generateIdToken with audience:", audience);

  const idTokenRes = await fetch(genUrl, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessTokenResponse.token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ audience, includeEmail: true }),
  });

  console.log("[auth] Step 3 generateIdToken HTTP status:", idTokenRes.status);

  if (!idTokenRes.ok) {
    const err = await idTokenRes.text();
    throw new Error(`generateIdToken failed (${idTokenRes.status}): ${err}`);
  }

  const rawBody = await idTokenRes.text();
  console.log("[auth] Step 3 raw response (first 200):", rawBody.slice(0, 200));

  let token: string;
  try {
    token = JSON.parse(rawBody).token;
  } catch (e) {
    throw new Error(`generateIdToken response parse failed: ${e}`);
  }

  console.log("[auth] Step 3 token length:", token?.length ?? "undefined");

  if (!token) {
    throw new Error(`generateIdToken returned no token. body: ${rawBody.slice(0, 300)}`);
  }

  // Decode and log the aud claim for debugging
  try {
    const payload = JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString());
    console.log("[auth] ID token aud:", payload.aud, "| iss:", payload.iss, "| email:", payload.email);
  } catch {}
  console.log("[auth] Step 3 OK: got ID token");
  return token;
}
