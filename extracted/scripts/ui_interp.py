"""Symbolic executor for Roblox UI-building Luau. Runs the script abstractly (no Roblox needed) and records
the Instance tree: classes, properties, parents, event hookups. Unknown values become UNK and never crash."""
import math
from ui_parse import parse, ParseError

class _Unk:
    def __repr__(self): return 'UNK'
    def __bool__(self): return True
UNK = _Unk()

GUI_CLASSES = {'ScreenGui', 'Frame', 'TextLabel', 'TextButton', 'TextBox', 'ImageLabel', 'ImageButton', 'ScrollingFrame',
               'CanvasGroup', 'ViewportFrame', 'VideoFrame', 'SurfaceGui', 'BillboardGui'}
MODIFIER_CLASSES = {'UIListLayout', 'UIGridLayout', 'UIPageLayout', 'UITableLayout', 'UIPadding', 'UICorner', 'UIStroke',
                    'UIGradient', 'UISizeConstraint', 'UIAspectRatioConstraint', 'UIScale', 'UITextSizeConstraint', 'UIFlexItem'}
KNOWN_CLASSES = GUI_CLASSES | MODIFIER_CLASSES | {'Folder', 'Sound', 'Part', 'LocalScript', 'ModuleScript', 'Script', 'BindableEvent', 'RemoteEvent', 'StringValue', 'NumberValue', 'BoolValue', 'IntValue', 'ObjectValue', 'Configuration', 'Model', 'Camera'}

class LTable:
    __slots__ = ('arr', 'hash', 'meta')
    def __init__(self): self.arr, self.hash, self.meta = [], {}, None
    def get(self, k):
        if isinstance(k, float) and k.is_integer(): k = int(k)
        if isinstance(k, int) and 1 <= k <= len(self.arr): return self.arr[k - 1]
        if k in self.hash: return self.hash[k]
        if self.meta is not None:
            idx = self.meta.hash.get('__index')
            if isinstance(idx, LTable): return idx.get(k)
        return None
    def set(self, k, v):
        if isinstance(k, float) and k.is_integer(): k = int(k)
        if isinstance(k, int) and 1 <= k <= len(self.arr):
            self.arr[k - 1] = v; return
        if isinstance(k, int) and k == len(self.arr) + 1 and v is not None:
            self.arr.append(v); return
        if v is None: self.hash.pop(k, None)
        else: self.hash[k] = v
    def length(self): return len(self.arr)

class OpenTable(LTable):
    """table whose missing keys read as UNK (used for services like game/Players)."""
    __slots__ = ()
    def get(self, k):
        v = LTable.get(self, k)
        return UNK if v is None else v

class Signal:
    def __init__(self, node, name): self.node, self.name = node, name

class Node:
    _n = 0
    def __init__(self, cls, line=0):
        Node._n += 1
        self.id = Node._n; self.cls = cls; self.props = {'Name': cls}; self.children = []; self.parent = None
        self.line = line; self.destroyed = False; self.handlers = set(); self.parented_unknown = False; self.unresolved = set()
    @property
    def name(self): return self.props.get('Name') if isinstance(self.props.get('Name'), str) else self.cls
    def set_parent(self, p):
        if self.parent is not None and self in self.parent.children: self.parent.children.remove(self)
        self.parent = p if isinstance(p, Node) else None
        self.parented_unknown = not isinstance(p, Node) and p is not None
        if isinstance(p, Node): p.children.append(self)
    def path(self):
        parts, n = [], self
        while n is not None: parts.append(n.name); n = n.parent
        return '.'.join(reversed(parts))

TOPBAR_H = 58
TOPBAR_LEFT_W = 172

def screen_region(node, vw, vh):
    """(x, y, w, h) a ScreenGui lays out in (mirrors ui_layout.Layouter.region_for)."""
    ignore = node.props.get('IgnoreGuiInset') is True
    si = node.props.get('ScreenInsets')
    si = si[2] if isinstance(si, tuple) and len(si) == 3 and si[0] == 'Enum' else None
    if ignore or si in ('None', 'DeviceSafeInsets'): return (0, 0, vw, vh)
    if si == 'TopbarSafeInsets': return (TOPBAR_LEFT_W, 0, max(vw - TOPBAR_LEFT_W, 0), TOPBAR_H + 2)
    return (0, TOPBAR_H, vw, max(vh - TOPBAR_H, 0))

class Func:
    def __init__(self, params, vararg, body, env, name=''):
        self.params, self.vararg, self.body, self.env, self.name = params, vararg, body, env, name

class Env:
    __slots__ = ('vars', 'parent')
    def __init__(self, parent=None): self.vars, self.parent = {}, parent
    def find(self, n):
        e = self
        while e is not None:
            if n in e.vars: return e
            e = e.parent
        return None
    def get(self, n):
        e = self.find(n); return e.vars[n] if e else UNK
    def set(self, n, v):
        e = self.find(n)
        (e or self).vars[n] = v
    def declare(self, n, v): self.vars[n] = v

class Return(Exception):
    def __init__(self, vals): self.vals = vals
class Break(Exception): pass
class Continue(Exception): pass
class Budget(Exception): pass

def truthy(v): return not (v is None or v is False)

class Interp:
    def __init__(self, max_steps=300000, viewport=None, touch=False):
        self.viewport, self.touch = viewport, touch
        self.nodes = []; self.cur_line = 0; self.line_stack = []; self.steps = 0; self.max_steps = max_steps; self.depth = 0
        self.skipped = 0; self.executed = 0; self.notes = []; self.g = Env()
        self._install_globals()
    # ---------- globals ----------
    def _install_globals(self):
        G = self.g
        inst = LTable(); inst.hash['new'] = self._b(self._instance_new)
        G.declare('Instance', inst)
        def dt(name, fn):
            t = LTable(); t.hash.update({k: self._b(v) for k, v in fn.items()}); G.declare(name, t)
        n = lambda v: v if isinstance(v, (int, float)) else 0
        dt('UDim2', {'new': lambda a: ('UDim2', n(a[0]), n(a[1]), n(a[2]), n(a[3])) if len(a) >= 4 and all(isinstance(x, (int, float)) for x in a[:4]) else (('UDim2', a[0][1], a[0][2], a[1][1], a[1][2]) if len(a) == 2 and isinstance(a[0], tuple) and isinstance(a[1], tuple) and a[0][0] == 'UDim' and a[1][0] == 'UDim' else (('UDim2', 0, 0, 0, 0) if not a else UNK)),
                     'fromScale': lambda a: ('UDim2', n(a[0]), 0, n(a[1]), 0) if len(a) >= 2 and all(isinstance(x, (int, float)) for x in a[:2]) else UNK,
                     'fromOffset': lambda a: ('UDim2', 0, n(a[0]), 0, n(a[1])) if len(a) >= 2 and all(isinstance(x, (int, float)) for x in a[:2]) else UNK})
        dt('UDim', {'new': lambda a: ('UDim', n(a[0]), n(a[1])) if len(a) >= 2 and all(isinstance(x, (int, float)) for x in a[:2]) else UNK})
        dt('Vector2', {'new': lambda a: ('V2', n(a[0]), n(a[1])) if len(a) >= 2 and all(isinstance(x, (int, float)) for x in a[:2]) else (('V2', 0, 0) if not a else UNK)})
        dt('Vector3', {'new': lambda a: ('V3',) + tuple(n(x) for x in a[:3]) if len(a) >= 3 else ('V3', 0, 0, 0)})
        def rgb(a):
            if len(a) >= 3 and all(isinstance(x, (int, float)) for x in a[:3]): return ('Color', int(a[0]), int(a[1]), int(a[2]))
            return UNK
        def c3new(a):
            if len(a) >= 3 and all(isinstance(x, (int, float)) for x in a[:3]): return ('Color', int(a[0] * 255), int(a[1] * 255), int(a[2] * 255))
            return UNK
        def hexc(a):
            if a and isinstance(a[0], str):
                h = a[0].lstrip('#')
                if len(h) == 6:
                    try: return ('Color', int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
                    except ValueError: pass
            return UNK
        dt('Color3', {'fromRGB': rgb, 'new': c3new, 'fromHex': hexc, 'fromHSV': lambda a: UNK})
        font = LTable(); font.hash.update({k: self._b(lambda a, k=k: ('Font', str(a[0]) if a and isinstance(a[0], str) else k)) for k in ('new', 'fromName', 'fromEnum', 'fromId')}); G.declare('Font', font)
        G.declare('Enum', ('EnumRoot',))
        # math
        m = LTable()
        def fl(f): return lambda a: f(a[0]) if a and isinstance(a[0], (int, float)) else UNK
        m.hash.update({'floor': self._b(fl(math.floor)), 'ceil': self._b(fl(math.ceil)), 'abs': self._b(fl(abs)), 'sqrt': self._b(fl(lambda x: math.sqrt(x) if x >= 0 else 0)),
                       'round': self._b(fl(lambda x: math.floor(x + 0.5))),
                       'max': self._b(lambda a: max(a) if a and all(isinstance(x, (int, float)) for x in a) else UNK),
                       'min': self._b(lambda a: min(a) if a and all(isinstance(x, (int, float)) for x in a) else UNK),
                       'clamp': self._b(lambda a: min(max(a[0], a[1]), a[2]) if len(a) >= 3 and all(isinstance(x, (int, float)) for x in a[:3]) else UNK),
                       'huge': float('inf'), 'pi': math.pi, 'random': self._b(lambda a: UNK)})
        G.declare('math', m)
        t = LTable()
        def tinsert(a):
            if a and isinstance(a[0], LTable):
                if len(a) == 2: a[0].arr.append(a[1])
                elif len(a) >= 3 and isinstance(a[1], (int, float)): a[0].arr.insert(int(a[1]) - 1, a[2])
            return None
        def tremove(a):
            if a and isinstance(a[0], LTable) and a[0].arr: return a[0].arr.pop(int(a[1]) - 1 if len(a) > 1 and isinstance(a[1], (int, float)) else -1)
            return None
        t.hash.update({'insert': self._b(tinsert), 'remove': self._b(tremove), 'unpack': self._b(lambda a: self._unpack(a)), 'getn': self._b(lambda a: len(a[0].arr) if a and isinstance(a[0], LTable) else UNK),
                       'clone': self._b(lambda a: self._clone_table(a[0]) if a and isinstance(a[0], LTable) else UNK)})
        G.declare('table', t)
        G.declare('ipairs', self._b(lambda a: ('iter', [(i + 1, v) for i, v in enumerate(a[0].arr)]) if a and isinstance(a[0], LTable) else UNK))
        G.declare('pairs', self._b(lambda a: ('iter', [(i + 1, v) for i, v in enumerate(a[0].arr)] + list(a[0].hash.items())) if a and isinstance(a[0], LTable) else UNK))
        G.declare('next', self._b(lambda a: UNK))
        G.declare('typeof', self._b(lambda a: self._typeof(a[0]) if a else UNK)); G.declare('type', G.get('typeof'))
        G.declare('tostring', self._b(lambda a: str(a[0]) if a and isinstance(a[0], (str, int, float)) else UNK))
        G.declare('tonumber', self._b(lambda a: self._tonumber(a[0]) if a else UNK))
        G.declare('select', self._b(lambda a: UNK)); G.declare('unpack', t.hash['unpack'])
        G.declare('print', self._b(lambda a: None)); G.declare('warn', G.get('print')); G.declare('error', self._b(lambda a: None)); G.declare('assert', self._b(lambda a: a[0] if a else None))
        G.declare('setmetatable', self._b(self._setmt)); G.declare('getmetatable', self._b(lambda a: a[0].meta if a and isinstance(a[0], LTable) else UNK))
        G.declare('pcall', self._b(self._pcall)); G.declare('rawget', self._b(lambda a: UNK)); G.declare('rawset', self._b(lambda a: UNK))
        task = LTable()
        def spawn(a):
            if a and isinstance(a[0], Func): self.call(a[0], a[1:])
            return UNK
        def delay(a):
            if len(a) >= 2 and isinstance(a[1], Func): self.call(a[1], a[2:])
            return UNK
        task.hash.update({'spawn': self._b(spawn), 'defer': self._b(spawn), 'delay': self._b(delay), 'wait': self._b(lambda a: 0.03), 'cancel': self._b(lambda a: None)})
        G.declare('task', task); G.declare('wait', task.hash['wait']); G.declare('spawn', task.hash['spawn']); G.declare('delay', task.hash['delay'])
        self._install_roblox_env()
    def _install_roblox_env(self):
        G = self.g
        vp = ('V2', self.viewport[0], self.viewport[1]) if self.viewport else UNK
        cam = OpenTable(); cam.hash['ViewportSize'] = vp
        ws = OpenTable(); ws.hash['CurrentCamera'] = cam
        player = OpenTable(); player.hash.update({'Name': 'Player', 'DisplayName': 'Player', 'UserId': 1})
        players = OpenTable(); players.hash['LocalPlayer'] = player
        uis = OpenTable(); uis.hash.update({'TouchEnabled': self.touch, 'KeyboardEnabled': not self.touch, 'MouseEnabled': not self.touch, 'GamepadEnabled': False})
        gs = OpenTable(); gs.hash['GetGuiInset'] = self._b(lambda a: [('V2', 0, 58), ('V2', 0, 0)])
        services = {'Players': players, 'UserInputService': uis, 'GuiService': gs, 'Workspace': ws}
        game = OpenTable(); game.hash['GetService'] = self._b(lambda a: services.get(a[1], UNK) if len(a) > 1 else UNK)
        game.hash.update({'Players': players, 'Workspace': ws})
        G.declare('game', game); G.declare('workspace', ws); G.declare('script', UNK)
    def _b(self, fn):
        return ('builtin', fn)
    def _unpack(self, a):
        return UNK
    def _clone_table(self, t):
        c = LTable(); c.arr = list(t.arr); c.hash = dict(t.hash); c.meta = t.meta; return c
    def _tonumber(self, v):
        if isinstance(v, (int, float)): return v
        if isinstance(v, str):
            try: return float(v)
            except ValueError: return None
        return UNK
    def _typeof(self, v):
        if v is UNK: return UNK
        if v is None: return 'nil'
        if isinstance(v, bool): return 'boolean'
        if isinstance(v, (int, float)): return 'number'
        if isinstance(v, str): return 'string'
        if isinstance(v, LTable): return 'table'
        if isinstance(v, (Func,)) or (isinstance(v, tuple) and v and v[0] == 'builtin'): return 'function'
        if isinstance(v, Node): return 'Instance'
        return 'userdata'
    def _setmt(self, a):
        if len(a) >= 2 and isinstance(a[0], LTable) and isinstance(a[1], LTable): a[0].meta = a[1]; return a[0]
        return a[0] if a else UNK
    def _pcall(self, a):
        if a and isinstance(a[0], Func):
            try: r = self.call_multi(a[0], a[1:]); return [True] + list(r)
            except (Return, Break, Continue): return [True]
        return [True]
    def _instance_new(self, a):
        cls = a[0] if a else UNK
        if not isinstance(cls, str):
            self.notes.append('Instance.new with non-literal class'); return UNK
        n = Node(cls, self.line_stack[-1] if self.line_stack else self.cur_line); self.nodes.append(n)
        if len(a) > 1 and a[1] is not UNK and a[1] is not None: n.set_parent(a[1])
        return n
    # ---------- evaluation ----------
    def tick(self):
        self.steps += 1
        if self.steps > self.max_steps: raise Budget()
    def run(self, body):
        env = Env(self.g)
        try:
            self.exec_block(body, env)
        except Budget:
            self.notes.append('execution budget reached (script too dynamic/long); layout may be partial')
        except Return:
            pass
        return env
    def exec_block(self, body, env):
        for s in body:
            self.tick()
            try:
                self.exec_stat(s, env)
            except (Return, Break, Continue, Budget):
                raise
            except RecursionError:
                self.skipped += 1
            except Exception as e:  # never crash on odd code
                self.skipped += 1
    def exec_stat(self, s, env):
        k = s[0]; self.executed += 1
        if k in ('local', 'assign', 'callstat') and isinstance(s[-1], int): self.cur_line = s[-1]
        if k == 'local':
            names, vals = s[1], s[2]
            vs = self.eval_list(vals, env)
            for i, n in enumerate(names):
                env.declare(n, vs[i] if i < len(vs) else None)
        elif k == 'localfunc':
            env.declare(s[1], Func(s[2][1], s[2][2], s[2][3], env, s[1]))
        elif k == 'assign':
            self.exec_assign(s, env)
        elif k == 'callstat':
            self.eval_multi(s[1], env)
        elif k == 'if':
            for c, b in zip(s[1], s[2]):
                cv = self.eval(c, env)
                if cv is UNK or truthy(cv):
                    self.exec_scope(b, env); return
            if s[3] is not None: self.exec_scope(s[3], env)
        elif k == 'numfor':
            a, b = self.eval(s[2], env), self.eval(s[3], env)
            st = self.eval(s[4], env) if s[4] else 1
            if all(isinstance(x, (int, float)) for x in (a, b, st)) and st != 0:
                i, cnt = a, 0
                while ((st > 0 and i <= b) or (st < 0 and i >= b)) and cnt < 400:
                    sub = Env(env); sub.declare(s[1], i)
                    try: self.exec_block(s[5], sub)
                    except Continue: pass
                    except Break: break
                    i += st; cnt += 1
            else:
                sub = Env(env); sub.declare(s[1], UNK)
                try: self.exec_block(s[5], sub)
                except (Break, Continue): pass
        elif k == 'genfor':
            it = self.eval(s[2][0], env) if s[2] else UNK
            pairs = None
            if isinstance(it, tuple) and it and it[0] == 'iter': pairs = it[1]
            elif isinstance(it, LTable): pairs = [(i + 1, v) for i, v in enumerate(it.arr)] + list(it.hash.items())
            if pairs is None:
                sub = Env(env)
                for n in s[1]: sub.declare(n, UNK)
                try: self.exec_block(s[3], sub)
                except (Break, Continue): pass
            else:
                for kk, vv in pairs[:400]:
                    sub = Env(env)
                    for j, n in enumerate(s[1]): sub.declare(n, kk if j == 0 else vv if j == 1 else None)
                    try: self.exec_block(s[3], sub)
                    except Continue: continue
                    except Break: break
        elif k == 'while':
            pass  # animation/update loops are not part of the static layout
        elif k == 'repeat':
            sub = Env(env)
            try: self.exec_block(s[1], sub)
            except (Break, Continue): pass
        elif k == 'do':
            self.exec_scope(s[1], env)
        elif k == 'return':
            raise Return(self.eval_list(s[1], env))
        elif k == 'break': raise Break()
        elif k == 'continue': raise Continue()
    def exec_scope(self, body, env):
        self.exec_block(body, Env(env))
    def exec_assign(self, s, env):
        targets, vals, op = s[1], s[2], s[3]
        if op != '=':
            cur = self.eval(targets[0], env); rhs = self.eval(vals[0], env)
            newv = self.binop(op[:-1], cur, rhs); self.assign_to(targets[0], newv, env); return
        vs = self.eval_list(vals, env)
        for i, t in enumerate(targets): self.assign_to(t, vs[i] if i < len(vs) else None, env)
    def assign_to(self, t, v, env):
        if t[0] == 'name':
            env.set(t[1], v)
        elif t[0] == 'index':
            obj = self.eval(t[1], env); key = self.eval(t[2], env)
            self.setindex(obj, key, v)
        elif t[0] == 'paren':
            self.assign_to(t[1], v, env)
    def setindex(self, obj, key, v):
        if isinstance(obj, LTable): obj.set(key, v)
        elif isinstance(obj, Node):
            if key == 'Parent':
                if v is UNK or v is None or isinstance(v, Node): obj.set_parent(v if v is not UNK else None); obj.parented_unknown = v is UNK
            else:
                obj.props[key] = v
                if v is UNK: obj.unresolved.add(key)
                else: obj.unresolved.discard(key)
    def eval_list(self, exprs, env):
        out = []
        for i, e in enumerate(exprs):
            if i == len(exprs) - 1 and e[0] in ('call', 'mcall', 'vararg'):
                out.extend(self.eval_multi(e, env))
            else:
                out.append(self.eval(e, env))
        return out
    def eval_multi(self, e, env):
        if e[0] == 'call':
            f = self.eval(e[1], env); args = self.eval_list(e[2], env)
            return self.call_multi(f, args)
        if e[0] == 'mcall':
            obj = self.eval(e[1], env); args = self.eval_list(e[3], env)
            return self.call_method(obj, e[2], args)
        if e[0] == 'vararg': return [UNK]
        return [self.eval(e, env)]
    def call_multi(self, f, args):
        self.tick()
        if isinstance(f, Func):
            if self.depth > 60: return [UNK]
            self.depth += 1; self.line_stack.append(self.cur_line)
            try:
                sub = Env(f.env)
                for i, p in enumerate(f.params): sub.declare(p, args[i] if i < len(args) else None)
                try: self.exec_block(f.body, sub)
                except Return as r: return r.vals if r.vals else [None]
                return [None]
            finally:
                self.depth -= 1; self.line_stack.pop()
        if isinstance(f, tuple) and f and f[0] == 'builtin':
            r = f[1](args)
            return r if isinstance(r, list) else [r]
        if isinstance(f, LTable) and f.meta is not None and isinstance(f.meta.hash.get('__call'), Func):
            return self.call_multi(f.meta.hash['__call'], [f] + list(args))
        return [UNK]
    def call(self, f, args):
        r = self.call_multi(f, args); return r[0] if r else None
    def call_method(self, obj, name, args):
        if isinstance(obj, Node): return self.node_method(obj, name, args)
        if isinstance(obj, LTable):
            f = obj.get(name)
            if f is not None: return self.call_multi(f, [obj] + list(args))
            return [UNK]
        if isinstance(obj, Signal):
            if name in ('Connect', 'Once'): obj.node.handlers.add(obj.name)
            return [UNK]
        return [UNK]
    def node_method(self, n, name, args):
        if name == 'Destroy' or name == 'Remove':
            n.set_parent(None)
            stack = [n]
            while stack:
                x = stack.pop(); x.destroyed = True; stack.extend(x.children)
            return [None]
        if name == 'Clone':
            return [self.clone_node(n)]
        if name in ('FindFirstChild', 'WaitForChild', 'FindFirstDescendant'):
            if args and isinstance(args[0], str):
                for c in (n.children if name != 'FindFirstDescendant' else self.descendants(n)):
                    if c.name == args[0]: return [c]
                return [UNK] if name == 'WaitForChild' else [None]
            return [UNK]
        if name == 'GetChildren':
            t = LTable(); t.arr = list(n.children); return [t]
        if name == 'GetDescendants':
            t = LTable(); t.arr = self.descendants(n); return [t]
        if name == 'SetAttribute': return [None]
        return [UNK]
    def descendants(self, n):
        out = []
        for c in n.children: out.append(c); out.extend(self.descendants(c))
        return out
    def clone_node(self, n):
        c = Node(n.cls, n.line); c.props = dict(n.props); c.handlers = set(n.handlers); self.nodes.append(c)
        for ch in n.children:
            cc = self.clone_node(ch); cc.set_parent(c)
        return c
    def eval(self, e, env):
        self.tick(); k = e[0]
        if k == 'num' or k == 'str' or k == 'bool': return e[1]
        if k == 'istr': return UNK
        if k == 'nil': return None
        if k == 'vararg': return UNK
        if k == 'name': return env.get(e[1])
        if k == 'paren': return self.eval(e[1], env)
        if k == 'table':
            t = LTable()
            for it in e[1]:
                if it[0] == 'arr':
                    v = self.eval(it[1], env); t.arr.append(v)
                elif it[0] == 'named': t.hash[it[1]] = self.eval(it[2], env)
                else:
                    kk = self.eval(it[1], env); vv = self.eval(it[2], env)
                    if kk is not UNK and kk is not None: t.set(kk, vv)
            return t
        if k == 'func': return Func(e[1], e[2], e[3], env)
        if k == 'index': return self.getindex(self.eval(e[1], env), self.eval(e[2], env))
        if k in ('call', 'mcall'):
            r = self.eval_multi(e, env); return r[0] if r else None
        if k == 'un':
            v = self.eval(e[2], env)
            if e[1] == '-': return -v if isinstance(v, (int, float)) else (self.udim2_neg(v) if isinstance(v, tuple) else UNK)
            if e[1] == 'not': return UNK if v is UNK else (not truthy(v))
            if e[1] == '#':
                if isinstance(v, LTable): return len(v.arr)
                if isinstance(v, str): return len(v)
                return UNK
        if k == 'bin':
            op = e[1]
            if op == 'and':
                l = self.eval(e[2], env)
                if l is UNK: return self.eval(e[3], env) if False else UNK
                return self.eval(e[3], env) if truthy(l) else l
            if op == 'or':
                l = self.eval(e[2], env)
                if l is UNK: return UNK
                return l if truthy(l) else self.eval(e[3], env)
            return self.binop(op, self.eval(e[2], env), self.eval(e[3], env))
        if k == 'ifexp':
            c = self.eval(e[1], env)
            if c is UNK: return self.eval(e[2], env)
            return self.eval(e[2], env) if truthy(c) else self.eval(e[3], env)
        return UNK
    def udim2_neg(self, v):
        if v and v[0] == 'UDim2': return ('UDim2', -v[1], -v[2], -v[3], -v[4])
        return UNK
    def binop(self, op, a, b):
        if a is UNK or b is UNK: return UNK
        try:
            if op == '..': return (str(a) + str(b)) if isinstance(a, (str, int, float)) and isinstance(b, (str, int, float)) else UNK
            if op in ('==', '~='):
                r = a == b if not (isinstance(a, Node) or isinstance(b, Node)) else a is b
                return r if op == '==' else not r
            if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
                if op == '+': return a + b
                if op == '-': return a - b
                if op == '*': return a * b
                if op == '/': return a / b if b else float('inf')
                if op == '//': return a // b if b else float('inf')
                if op == '%': return a % b if b else float('nan')
                if op == '^': return a ** b
                if op == '<': return a < b
                if op == '>': return a > b
                if op == '<=': return a <= b
                if op == '>=': return a >= b
            if isinstance(a, tuple) and isinstance(b, tuple) and a and b and a[0] == b[0]:
                if a[0] == 'UDim2' and op in ('+', '-'):
                    s = 1 if op == '+' else -1
                    return ('UDim2', a[1] + s * b[1], a[2] + s * b[2], a[3] + s * b[3], a[4] + s * b[4])
                if a[0] == 'UDim' and op in ('+', '-'):
                    s = 1 if op == '+' else -1
                    return ('UDim', a[1] + s * b[1], a[2] + s * b[2])
                if a[0] == 'V2' and op in ('+', '-'):
                    s = 1 if op == '+' else -1
                    return ('V2', a[1] + s * b[1], a[2] + s * b[2])
            if isinstance(a, tuple) and a and a[0] == 'V2' and isinstance(b, (int, float)):
                if op == '*': return ('V2', a[1] * b, a[2] * b)
                if op == '/' and b: return ('V2', a[1] / b, a[2] / b)
            if isinstance(a, (int, float)) and isinstance(b, tuple) and b and b[0] == 'V2' and op == '*': return ('V2', b[1] * a, b[2] * a)
        except Exception:
            return UNK
        return UNK
    def getindex(self, obj, key):
        if obj is UNK or obj is None: return UNK
        if isinstance(obj, LTable):
            v = obj.get(key); return v
        if isinstance(obj, Node):
            if key in obj.props: return obj.props[key]
            if key == 'Parent': return obj.parent if obj.parent is not None else (UNK if obj.parented_unknown else None)
            if key == 'ClassName': return obj.cls
            if key in ('AbsoluteSize', 'AbsolutePosition') and obj.cls == 'ScreenGui' and self.viewport:
                x, y, w, h = screen_region(obj, self.viewport[0], self.viewport[1])
                return ('V2', w, h) if key == 'AbsoluteSize' else ('V2', x, y)
            if key in ('AbsoluteSize', 'AbsolutePosition', 'TextBounds', 'AbsoluteContentSize'): return UNK
            for c in obj.children:
                if c.name == key: return c
            if isinstance(key, str) and key[:1].isupper() and (key.startswith('Mouse') or key in ('Activated', 'InputBegan', 'InputEnded', 'InputChanged', 'TouchTap', 'FocusLost', 'Changed', 'ChildAdded', 'Touched')):
                return Signal(obj, key)
            return self.default_prop(obj, key)
        if isinstance(obj, tuple) and obj:
            if obj[0] == 'EnumRoot': return ('EnumType', key)
            if obj[0] == 'EnumType': return ('Enum', obj[1], key)
            if obj[0] == 'UDim2':
                m = {'X': ('UDim', obj[1], obj[2]), 'Y': ('UDim', obj[3], obj[4]), 'Width': ('UDim', obj[1], obj[2]), 'Height': ('UDim', obj[3], obj[4])}
                return m.get(key, UNK)
            if obj[0] == 'UDim': return {'Scale': obj[1], 'Offset': obj[2]}.get(key, UNK)
            if obj[0] == 'V2': return {'X': obj[1], 'Y': obj[2]}.get(key, UNK)
            if obj[0] == 'Color': return {'R': obj[1] / 255, 'G': obj[2] / 255, 'B': obj[3] / 255}.get(key, UNK)
        return UNK
    def default_prop(self, n, key):
        return UNK
