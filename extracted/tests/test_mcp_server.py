import json, subprocess, sys
from pathlib import Path
SERVER = str(Path(__file__).parents[1] / "mcp" / "luau_validator_mcp.py")

def rpc(*msgs):
    p = subprocess.run([sys.executable, SERVER], input="\n".join(json.dumps(m) for m in msgs) + "\n",
                       capture_output=True, text=True, timeout=30)
    return [json.loads(l) for l in p.stdout.splitlines()]

def test_handshake_and_tools():
    out = rpc({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26"}},
              {"jsonrpc":"2.0","method":"notifications/initialized"},
              {"jsonrpc":"2.0","id":2,"method":"tools/list"})
    assert len(out) == 2 and out[0]["result"]["serverInfo"]["name"] == "luau-validator-bridge"
    names = {t["name"] for t in out[1]["result"]["tools"]}
    assert {"validate_external_luau", "validate_luau_syntax", "server_status"} <= names

def test_level2_tool():
    out = rpc({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"validate_luau_syntax","arguments":{"code":"local x = (1+2)/3"}}})
    assert json.loads(out[0]["result"]["content"][0]["text"])["status"] == "SYNTAX_VERIFIED"

def test_unknown_tool_errors():
    out = rpc({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"nope"}})
    assert out[0]["error"]["code"] == -32602
