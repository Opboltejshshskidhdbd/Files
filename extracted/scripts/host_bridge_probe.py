#!/usr/bin/env python3
"""Probe the optional host validator bridge without pretending it exists.

The local package cannot manufacture a host MCP action. A real bridge may be
supplied by the host via the documented contract. Without one this script
returns VALIDATION_UNAVAILABLE and never labels the source verified.
"""
import json, os, sys

def main():
    bridge = os.environ.get("ROBLOX_DEV_MASTER_VALIDATOR_BRIDGE")
    if not bridge:
        print(json.dumps({
            "status": "VALIDATION_UNAVAILABLE",
            "validator_host_callable": False,
            "reason": "No host validator bridge was injected by the execution environment.",
        }, indent=2))
        return 2
    print(json.dumps({
        "status": "VALIDATION_BLOCKED",
        "validator_host_callable": False,
        "reason": "Bridge discovery requires an approved host tool adapter; arbitrary command execution is intentionally not performed.",
        "configured_bridge": bridge,
    }, indent=2))
    return 3

if __name__ == "__main__":
    raise SystemExit(main())
