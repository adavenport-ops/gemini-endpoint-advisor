"""Command-line entrypoint for Gemini Endpoint Advisor."""

from __future__ import annotations

import argparse
from collections import Counter
from typing import Any, Dict, List

from .jamf_client import JamfClient
from .gemini_advisor import GeminiEndpointAdvisor
from .config import load_config


def _parse_version(version: str) -> float:
    parts = version.split(".")
    if not parts:
        return 0.0
    if len(parts) == 1:
        return float(parts[0])
    # major.minor as float, e.g. "14.5" -> 14.5
    return float(f"{parts[0]}.{parts[1]}")


def _is_version_compliant(
    os_version: str,
    min_version: str,
    fv_enabled: bool,
    fw_enabled: bool,
    require_fv: bool,
    require_fw: bool,
) -> bool:
    """Very simple version and control compliance check.

    For this prototype we only care that the device is:
    - on or above `min_version`
    - has FileVault enabled if required
    - has firewall enabled if required
    """
    try:
        version_ok = _parse_version(os_version) >= _parse_version(min_version)
    except Exception:
        version_ok = False

    fv_ok = (not require_fv) or fv_enabled
    fw_ok = (not require_fw) or fw_enabled
    return version_ok and fv_ok and fw_ok


def build_fleet_snapshot(
    devices: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """Build a compact snapshot of fleet posture from Jamf devices."""
    os_counts: Counter[str] = Counter()
    fv_disabled = 0
    firewall_disabled = 0
    noncompliant = 0

    min_macos = config.get("min_macos_version", "14.0")
    require_fv = bool(config.get("require_filevault", True))
    require_fw = bool(config.get("require_firewall", True))

    for d in devices:
        os_info = d.get("operatingSystem", {}) or {}
        os_version = os_info.get("version", "unknown") or "unknown"
        os_counts[os_version] += 1

        security = d.get("security", {}) or {}
        fv_enabled = bool(security.get("fileVaultEnabled", False))
        fw_enabled = bool(security.get("firewallEnabled", False))

        if require_fv and not fv_enabled:
            fv_disabled += 1
        if require_fw and not fw_enabled:
            firewall_disabled += 1

        if os_version != "unknown":
            if not _is_version_compliant(
                os_version=os_version,
                min_version=min_macos,
                fv_enabled=fv_enabled,
                fw_enabled=fw_enabled,
                require_fv=require_fv,
                require_fw=require_fw,
            ):
                noncompliant += 1

    total = len(devices)
    pct_noncompliant = (noncompliant / total * 100) if total > 0 else 0.0

    snapshot: Dict[str, Any] = {
        "total_devices": total,
        "os_version_breakdown": dict(os_counts),
        "filevault_disabled_count": fv_disabled,
        "firewall_disabled_count": firewall_disabled,
        "noncompliant_count": noncompliant,
        "noncompliant_percentage": round(pct_noncompliant, 2),
        "min_macos_version": min_macos,
        "require_filevault": require_fv,
        "require_firewall": require_fw,
        "max_noncompliant_percentage": config.get("max_noncompliant_percentage", 10),
    }

    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gemini-powered Jamf endpoint posture advisor",
    )
    parser.add_argument(
        "--max-devices",
        type=int,
        default=100,
        help="Maximum number of devices to fetch from Jamf",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to YAML config file (optional)",
    )

    args = parser.parse_args()

    config = load_config(args.config)
    jamf = JamfClient()
    advisor = GeminiEndpointAdvisor()

    devices = jamf.get_computers_inventory(max_devices=args.max_devices)
    if not devices:
        print("No devices returned from Jamf Pro.")
        return

    snapshot = build_fleet_snapshot(devices, config)
    advice = advisor.analyze_fleet(snapshot)

    print("=== Endpoint Posture Summary ===\n")
    print(advice.get("summary", "").strip())
    print("\n=== Remediation Plan ===\n")
    print(advice.get("remediation_plan", "").strip())
    print("\n=== Slack Message ===\n")
    print(advice.get("slack_message", "").strip())


if __name__ == "__main__":
    main()
