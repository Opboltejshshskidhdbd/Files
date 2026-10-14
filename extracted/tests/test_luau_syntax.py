import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
from luau_syntax import validate_source, validate_luau_files

def ok(src):
    r=validate_source(src).to_dict(); assert r['status']=='SYNTAX_VERIFIED', r
def bad(src):
    assert validate_source(src).to_dict()['status']=='SYNTAX_FAILED'

def test_roblox_realistic():
    ok('''local Players = game:GetService("Players")\nlocal ReplicatedStorage = game:GetService("ReplicatedStorage")\nlocal Remote = ReplicatedStorage:WaitForChild("Remote")\nRemote.OnServerEvent:Connect(function(player, ...)\n    if player then\n        task.spawn(function() print(player.Name) end)\n    end\nend)''')

def test_nested_callbacks_and_services():
    ok('''local RunService = game:GetService("RunService")\nlocal TweenService = game:GetService("TweenService")\nRunService.Heartbeat:Connect(function(dt)\n  task.defer(function()\n    local x = Instance.new("Part")\n    x.CFrame = CFrame.new(Vector3.new(1,2,3))\n    if dt > 0 then\n      TweenService:Create(x, TweenInfo.new(1), {Transparency=1}):Play()\n    end\n  end)\nend)''')

def test_types_generics_casts_module():
    ok('''export type Item = { id: string, value: number? }\ntype Box<T> = { value: T }\nlocal function id<T>(x: T): T return x end\nlocal x = (id<number>(3) :: number)\nreturn {x=x}''')

def test_repeat_pcall_task_prompt_ui():
    ok('''local ok, result = pcall(function()\n  repeat\n    task.spawn(function() end)\n  until true\nend)\nlocal gui = Instance.new("ScreenGui")\ngui.Enabled = ok''')

def test_long_strings_comments_interpolation():
    ok('-- comment\nlocal a=[[hello\nworld]]\nlocal b=`value {1}`\nreturn a..b')

def test_extra_end(): bad('local x=1\nend')
def test_missing_end(): bad('if true then\n print(1)')
def test_multiple_structural_errors(): bad('if true then\n function f()\n  if false then\n   print(1)\n')
def test_repeat_until_errors(): bad('repeat print(1) end')
def test_malformed_function(): bad('function )')
def test_hash_idempotent():
    src='local x = 1\nif x > 0 then print(x) end'
    a=validate_source(src); b=validate_source(src)
    assert a.source_hash==b.source_hash and a.diagnostics==b.diagnostics and src=='local x = 1\nif x > 0 then print(x) end'

def test_multifile():
    r=validate_luau_files({'A.server.lua':'local x=1','B.client.lua':'if true then\n'})
    assert r['status']=='SYNTAX_FAILED' and 'B.client.lua' in r['files_checked']


def test_parenthesised_expressions():
    ok('local a = (os.clock() - 1) / 2\n(f or g)()\nlocal t = (a)')

def test_dotted_and_method_function_names():
    ok('local V = {}\nfunction V.new(x) return x end\nfunction V.a.b:go() end')

def test_prose_is_rejected():
    bad('Problem: this is just prose, not code.')

def test_type_syntax_optional_union_typeof():
    ok('export type Item = { id: string, value: number? }\ntype U = string | number | nil\n'
       'type F = (a: number, b: string?) -> boolean\ntype M = typeof(setmetatable({}, {}))\n'
       'local m: Mod.Item? = nil')

def test_soft_keywords_are_identifiers():
    ok('local t = type(x)\nif type(x) == "table" then end\nlocal export = 1\nprint(export)')
