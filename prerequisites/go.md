# Course Prerequisites (Go)

Welcome to the Building Multi-Agent Systems with ADK Masterclass! To ensure a smooth experience coding alongside the lectures, please verify that you have the following tools and accounts set up before starting Section 1.

## 1. Core Tooling
* **[Go (v1.24+)](https://go.dev/doc/install)**: The core Go compiler and tooling.
* **[Go ADK](https://github.com/google/adk-go)**: The Go ADK library for building agents.

## 2. Infrastructure & Cloud Setup
* **[Google Cloud CLI (gcloud)](https://cloud.google.com/sdk/docs/install)**: Required to authenticate your local machine with Google Cloud.
    * *Post-install action:* Run `gcloud auth application-default login` in your terminal.
* **[Terraform](https://developer.hashicorp.com/terraform/downloads)** (Optional but Recommended): We will use this for Infrastructure as Code. You may also use the `gcloud` CLI if you prefer.
* **Google Cloud Project**:
    * An active GCP project with **Billing Enabled**.
    * Ensure the following APIs are enabled in your console: `Vertex AI API`, `Cloud Run API`, `Secret Manager API`, and `Artifact Registry API`.

## 3. Third-Party API Credentials
We will be building real-world integrations. Please generate and save these keys securely.

for more information see: [Go ADK Get Started](https://google.github.io/adk-docs/get-started/go/)
