# Course Prerequisites (Python)

Welcome to the Building Multi-Agent Systems with ADK Masterclass! To ensure a smooth experience coding alongside the lectures, please verify that you have the following tools and accounts set up before starting Section 1.

## 1. Core Tooling
* **[Python 3.12+](https://www.python.org/downloads/)**: The core runtime for our agents.
* **[uv (Python Package Manager)](https://docs.astral.sh/uv/getting-started/installation/)**: We use `uv` for lightning-fast, reproducible virtual environments.
    * *Mac/Linux Install:* `curl -LsSf https://astral.sh/uv/install.sh | sh`
    * *Windows Install:* `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
* **[Node.js (LTS) & npm](https://nodejs.org/en/download)**: Required to run the local `adk web` UI playbook and frontend components.

## 2. Infrastructure & Cloud Setup
* **[Google Cloud CLI (gcloud)](https://cloud.google.com/sdk/docs/install)**: Required to authenticate your local machine with Google Cloud.
    * *Post-install action:* Run `gcloud auth application-default login` in your terminal.
* **[Terraform](https://developer.hashicorp.com/terraform/downloads)** (Optional but Recommended): We will use this for Infrastructure as Code. You may also use the `gcloud` CLI if you prefer.
* **Google Cloud Project**:
    * An active GCP project with **Billing Enabled**.
    * Ensure the following APIs are enabled in your console: `Vertex AI API`, `Cloud Run API`, `Secret Manager API`, and `Artifact Registry API`.

## 3. Third-Party API Credentials
We will be building real-world integrations. Please generate and save these keys securely (we will store them in a `.env` file during the course).

for more information see: [Python ADK Get Started](https://google.github.io/adk-docs/get-started/python/)
