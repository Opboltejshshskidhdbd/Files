#!/usr/bin/env python3
"""Luau Validator Bridge - local stdio MCP server (stdlib only, Python 3.9+).

Tools:
  validate_external_luau  Level 3: POST exact source to the external validator.
  validate_luau_syntax    Level 2: bundled structural/syntax parser (offline).
  server_status           Self-check: shows tool list, endpoint and reachability.

Transport: newline-delimited JSON-RPC 2.0 on stdin/stdout. Logs go to stderr only.
"""
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import external_luau_validator as ext  # noqa: E402
from luau_syntax import validate_source  # noqa: E402

SERVER = {"name": "luau-validator-bridge", "version": "1.14.1"}
DEFAULT_PROTOCOL = "2025-03-26"
ENDPOINT = os.environ.get("LUAU_VALIDATOR_ENDPOINT", ext.ENDPOINT)

CODE_PROP = {"type": "string", "description": "Exact, unmodified Luau source."}
NAME_PROP = {"type": "string", "description": "Optional file/script name for the receipt."}
TOOLS = [
    {"name": "validate_external_luau",
     "description": "Level 3: send the exact Luau source to the external Luau validator and return a receipt "
                    "(status EXTERNAL_VALIDATION_PASSED/FAILED/UNAVAILABLE, errors, warnings, source hash).",
     "inputSchema": {"type": "object", "properties": {"code": CODE_PROP, "source_name": NAME_PROP,
                                                       "attempt": {"type": "integer", "minimum": 1}},
                     "required": ["code"]}},
    {"name": "validate_luau_syntax",
     "description": "Level 2: offline bundled Luau structural/syntax parser (not the official compiler).",
     "inputSchema": {"type": "object", "properties": {"code": CODE_PROP, "source_name": NAME_PROP},
                     "required": ["code"]}},
    {"name": "server_status",
     "description": "Report server version, endpoint and whether the external validator is reachable.",
     "inputSchema": {"type": "object", "properties": {}}},
]


def _text(obj, error=False):
    return {"content": [{"type": "text", "text": json.dumps(obj, indent=2, ensure_ascii=False)}], "isError": error}


def call_tool(name, args):
    args = args or {}
    if name == "validate_external_luau":
        code = args.get("code")
        if not isinstance(code, str):
            return _text({"status": "EXTERNAL_VALIDATION_UNAVAILABLE", "failure_reason": "MISSING_CODE"}, True)
        r = ext.ExternalLuauValidator(ENDPOINT).validate_exact(
            code, args.get("source_name") or "<source>", int(args.get("attempt") or 1))
        return _text(r, r["status"] == ext.EXTERNAL_VALIDATION_UNAVAILABLE)
    if name == "validate_luau_syntax":
        code = args.get("code")
        if not isinstance(code, str):
            return _text({"status": "SYNTAX_FAILED", "message": "'code' must be a string"}, True)
        return _text(validate_source(code, args.get("source_name") or "<source>"))
    if name == "server_status":
        probe = ext.ExternalLuauValidator(ENDPOINT, timeout=8).validate_exact("local x = 1\n", "<probe>")
        return _text({"server": SERVER, "tools": [t["name"] for t in TOOLS], "endpoint": ENDPOINT,
                      "external_status": probe["status"], "failure_reason": probe.get("failure_reason"),
                      "api_http_status": probe.get("api_http_status")})
    return None


def handle(msg):
    method, mid, params = msg.get("method"), msg.get("id"), msg.get("params") or {}
    if mid is None:  # notification
        return None
    def ok(result): return {"jsonrpc": "2.0", "id": mid, "result": result}
    def err(code, m): return {"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": m}}
    if method == "initialize":
        return ok({"protocolVersion": params.get("protocolVersion") or DEFAULT_PROTOCOL,
                   "capabilities": {"tools": {"listChanged": False}}, "serverInfo": SERVER})
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": TOOLS})
    if method == "tools/call":
        try:
            res = call_tool(params.get("name"), params.get("arguments"))
        except Exception as exc:  # never crash the server
            return ok(_text({"status": "EXTERNAL_VALIDATION_UNAVAILABLE", "failure_reason": "SERVER_EXCEPTION",
                             "message": repr(exc)}, True))
        return ok(res) if res is not None else err(-32602, f"Unknown tool: {params.get('name')}")
    if method in ("resources/list", "prompts/list"):
        return ok({method.split("/")[0]: []})
    return err(-32601, f"Method not found: {method}")


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            print(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}), flush=True)
            continue
        out = handle(msg) if isinstance(msg, dict) else None
        if out is not None:
            print(json.dumps(out, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
