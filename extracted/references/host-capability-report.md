# Host Capability Report — Level 3 External Luau Validator (v1.14.1)

| Capability | Result | Evidence |
|---|---|---|
| Level 1 Engineering Gate | PRESENT | skills/roblox-engineering-enforcement |
| Level 2 bundled parser | PRESENT, regression-tested | scripts/luau_parser.py, tests/ |
| Level 3 client | PRESENT | scripts/external_luau_validator.py |
| Level 3 MCP bridge | PRESENT: worker `/mcp` (default) + local stdio | JSON-RPC tested locally against worker code and mcp/luau_validator_mcp.py |
| Live call to the external endpoint | MUST BE VERIFIED ON THE USER'S MACHINE | run the `server_status` MCP tool |

A packaged tool is not execution evidence. `EXTERNAL_VALIDATION_PASSED` requires an actual successful POST for the exact source.
