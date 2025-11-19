# Gemini Endpoint Advisor

AI-powered endpoint compliance and remediation assistant for Jamf Pro using Google's Gemini.

This tool:

- Fetches macOS inventory from Jamf Pro via the modern REST API
- Builds a compact "fleet posture" snapshot (OS versions, FileVault, firewall, basic compliance)
- Uses Gemini to generate:
  - A plain-English summary of endpoint posture
  - A remediation plan (Jamf smart groups, policies, baseline ideas)
  - A Slack-ready summary

## Features

- **Jamf Pro integration** using bearer token auth (`/api/v1/auth/token`)
- **Config-as-code** via a small YAML file (`configs/example_config.yaml`)
- **Gemini integration** using the official `google-genai` Python SDK
- Installable as a CLI: `gemini-endpoint-advisor`

> This is a proof-of-concept for AI-assisted client platform operations, not a production system.  
> It is intentionally simple and self-contained so it is easy to read and extend.

---

## Installation

```bash
git clone https://github.com/your-username/gemini-endpoint-advisor.git
cd gemini-endpoint-advisor

python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

pip install -e .
```

---

## Configuration

### 1. Jamf & Gemini credentials

Set the following environment variables:

```bash
export GEMINI_API_KEY="your_gemini_api_key"

export JAMF_BASE_URL="https://your-jamf-url.example.com"
export JAMF_CLIENT_ID="your-oauth-client-id"
export JAMF_CLIENT_SECRET="your-oauth-client-secret"
```

### 2. Policy config (YAML)

Edit `configs/example_config.yaml` or create your own:

```yaml
min_macos_version: "14.5"
max_versions_behind: 2
require_filevault: true
require_firewall: true
max_noncompliant_percentage: 10
slack:
  title: "Weekly Endpoint Posture Summary"
  channel: "#client-platform"
  include_emojis: true
```

You can pass the config path via `--config` or set:

```bash
export GEMINI_ENDPOINT_ADVISOR_CONFIG="configs/example_config.yaml"
```

---

## Usage

Fetch up to 150 devices from Jamf and generate a report:

```bash
gemini-endpoint-advisor --config configs/example_config.yaml --max-devices 150
```

Example output:

```text
=== Endpoint Posture Summary ===
<Gemini summary here>

=== Remediation Plan ===
<Gemini remediation recommendations here>

=== Slack Message ===
<Slack-formatted summary here>
```

---

## Development notes

- Python 3.10+
- Code is intentionally concise and heavily commented to make it easy to review in an interview.
- You can extend this to:
  - Post directly into Slack via a webhook
  - Export results into Airtable / dashboards
  - Add richer compliance logic (CIS, internal baselines, etc.)
