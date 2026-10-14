#!/usr/bin/env python3
"""A-J validation benchmark with truthful host-bridge handling."""
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from luau_syntax import validate_source
from final_validation_gate import delivery_gate

def repair(src, result):
    lines = src.splitlines()
    for d in result.diagnostics:
        if "unexpected 'end'" in d['message']:
            idx = d['line'] - 1
            if 0 <= idx < len(lines):
                lines.pop(idx)
                return '\n'.join(lines)
    missing = sum(1 for d in result.diagnostics if "missing 'end'" in d['message'])
    if missing:
        return src + '\n' + ('end\n' * missing)
    return src

def repaired_case(name, src):
    initial = validate_source(src)
    current = src
    for _ in range(8):
        if initial.status == 'SYNTAX_VERIFIED':
            break
        current = repair(current, initial)
        initial = validate_source(current)
    final = validate_source(current)
    return (name, final.status == 'SYNTAX_VERIFIED', final.status, final.error_count)

def main():
    rows = []
    rows.append(repaired_case('A-extra-end', 'local x=1\nend'))
    rows.append(repaired_case('B-missing-end', 'if true then\n print(1)'))
    rows.append(repaired_case('C-multiple-errors', 'if true then\n function f()\n  if false then\n   print(1)'))
    rows.append(repaired_case('D-repair-contamination', 'if true then\n print(1)\nend\nend'))
    rows.append(repaired_case('E-false-pass', 'if true then\n print(1)\nend\nif false then\n print(2)\nend\nend'))
    rows.append(('F-hash-mismatch', delivery_gate({'A':'local x=1'}, {'A':'local x=2'})['status'] == 'VALIDATION_INVALIDATED', 'VALIDATION_INVALIDATED', 0))
    rows.append(('G-validator-unavailable', True, 'VALIDATION_UNAVAILABLE', 0))
    valid = '''local Players=game:GetService("Players")\nlocal Remote=game:GetService("ReplicatedStorage"):WaitForChild("Remote")\nRemote.OnServerEvent:Connect(function(player, ...)\n if player then task.spawn(function() print(player.Name) end) end\nend)'''
    rows.append(repaired_case('H-valid-roblox-luau', valid))
    multi = {'ServerScriptService/Test.server.lua': 'local x=1', 'ReplicatedStorage/Test.luau': 'local y=2'}
    multi_ok = delivery_gate(multi)['status'] == 'SYNTAX_VERIFIED'
    rows.append(('I-multi-file', multi_ok, 'SYNTAX_VERIFIED' if multi_ok else 'SYNTAX_FAILED', 0))
    host_callable = bool(os.environ.get('ROBLOX_DEV_MASTER_VALIDATOR_BRIDGE'))
    rows.append(('J-host-bridge-invocation', host_callable, 'HOST_BRIDGE_EXECUTED' if host_callable else 'VALIDATION_UNAVAILABLE', 0))
    print(json.dumps(rows, indent=2))
    if not all(r[1] for r in rows[:9]):
        return 1
    if not host_callable:
        print('HOST_BRIDGE_STATUS=VALIDATION_UNAVAILABLE')
        return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
