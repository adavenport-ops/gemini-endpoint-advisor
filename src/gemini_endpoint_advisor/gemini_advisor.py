"""Gemini integration and fleet analysis helper."""

from __future__ import annotations

import json
from typing import Any, Dict

from google import genai  # type: ignore


class GeminiEndpointAdvisor:
    """Wrapper around the Gemini client for endpoint posture analysis.

    By default this will look for the GEMINI_API_KEY environment variable.
    """

    def __init__(self, model: str = "gemini-2.5-flash") -> None:
        self.client = genai.Client()
        self.model = model

    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini with a simple text prompt and return the text.

        Errors are allowed to propagate so the CLI can fail fast and loudly.
        """
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        # The google-genai client exposes .text for the combined text output.
        return getattr(response, "text", "") or ""

    def analyze_fleet(self, fleet_snapshot: Dict[str, Any]) -> Dict[str, str]:
        """Ask Gemini to analyze the given fleet snapshot.

        The snapshot should be a small, JSON-serializable dict with fields
        like:

        - total_devices
        - os_version_breakdown
        - filevault_disabled_count
        - firewall_disabled_count
        - noncompliant_count
        - noncompliant_percentage
        """
        pretty_snapshot = json.dumps(fleet_snapshot, indent=2, sort_keys=True)

        base_prompt = f"""You are a senior endpoint engineer and security-conscious
client platform owner. You are reviewing a Jamf Pro-managed macOS fleet.

You are given the following JSON describing fleet posture:

```json
{pretty_snapshot}
```

1. Write a concise plain-English summary (2–3 paragraphs) of the current fleet posture.
2. Propose concrete remediation steps suitable for Jamf Pro:
   - smart group logic ideas
   - policy changes
   - zero-touch / baseline improvements
3. Generate a Slack-ready summary with bullets and emojis titled "Weekly Endpoint Posture Summary".

Return your answer in *valid JSON* with this structure:

{{
  "summary": "...",
  "remediation_plan": "...",
  "slack_message": "..."
}}""".strip()

        raw = self._call_gemini(base_prompt).strip()

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            # As a safety net, if Gemini answered with Markdown or text,
            # wrap it into the expected structure instead of crashing.
            return {
                "summary": raw,
                "remediation_plan": "",
                "slack_message": "",
            }

        return {
            "summary": str(parsed.get("summary", "")),
            "remediation_plan": str(parsed.get("remediation_plan", "")),
            "slack_message": str(parsed.get("slack_message", "")),
        }
