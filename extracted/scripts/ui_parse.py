"""Luau subset tokenizer + parser used by the UI layout engine (pure Python, no dependencies).
It builds an AST good enough to *symbolically execute* UI-building code. Type annotations are skipped.
Anything it cannot parse raises ParseError (callers degrade gracefully)."""
import re

class ParseError(Exception):
    pass

KEYWORDS = {'and','break','do','else','elseif','end','false','for','function','if','in','local','nil','not','or','repeat','return','then','true','until','while'}
SYMS3 = ['...', '..=', '//=']
SYMS2 = ['==','~=','<=','>=','..','->','::','+=','-=','*=','/=','%=','^=','//']
NUM_RE = re.compile(r'0[xX][0-9a-fA-F_]+|0[bB][01_]+|(?:\d[\d_]*\.(?!\.)[\d_]*|\.\d[\d_]*|\d[\d_]*)(?:[eE][+-]?\d+)?')
ID_RE = re.compile(r'[A-Za-z_][A-Za-z_0-9]*')

class Tok:
    __slots__ = ('t', 'v', 'line')
    def __init__(self, t, v, line):
        self.t, self.v, self.line = t, v, line
    def __repr__(self):
        return f'{self.t}:{self.v}'

def tokenize(src):
    toks, i, n, line = [], 0, len(src), 1
    while i < n:
        c = src[i]
        if c == '\n':
            line += 1; i += 1; continue
        if c in ' \t\r':
            i += 1; continue
        if src.startswith('--', i):
            m = re.match(r'--\[(=*)\[', src[i:])
            if m:
                close = ']' + m.group(1) + ']'
                j = src.find(close, i + len(m.group(0)))
                j = n if j < 0 else j + len(close)
                line += src.count('\n', i, j); i = j
            else:
                j = src.find('\n', i); i = n if j < 0 else j
            continue
        m = re.match(r'\[(=*)\[', src[i:])
        if c == '[' and m:
            close = ']' + m.group(1) + ']'
            j = src.find(close, i + len(m.group(0)))
            if j < 0: raise ParseError('unterminated long string')
            toks.append(Tok('str', src[i + len(m.group(0)):j], line))
            line += src.count('\n', i, j); i = j + len(close); continue
        if c in '"\'`':
            j = i + 1; buf = []
            while j < n and src[j] != c:
                if src[j] == '\\' and j + 1 < n:
                    esc = src[j + 1]
                    buf.append({'n': '\n', 't': '\t'}.get(esc, esc)); j += 2; continue
                if src[j] == '\n' and c != '`': raise ParseError(f'unterminated string line {line}')
                if src[j] == '\n': line += 1
                buf.append(src[j]); j += 1
            if j >= n: raise ParseError('unterminated string')
            toks.append(Tok('istr' if c == '`' else 'str', ''.join(buf), line)); i = j + 1; continue
        if c.isdigit() or (c == '.' and i + 1 < n and src[i + 1].isdigit()):
            m = NUM_RE.match(src, i)
            txt = m.group(0).replace('_', '')
            try:
                if txt[:2].lower() == '0x': v = int(txt, 16)
                elif txt[:2].lower() == '0b': v = int(txt, 2)
                else:
                    v = float(txt)
                    if v.is_integer() and not any(ch in txt for ch in '.eE'): v = int(v)
            except ValueError:
                raise ParseError(f'bad number {txt}')
            toks.append(Tok('num', v, line)); i = m.end(); continue
        m = ID_RE.match(src, i)
        if m:
            w = m.group(0)
            toks.append(Tok('kw' if w in KEYWORDS else 'id', w, line)); i = m.end(); continue
        for s in SYMS3:
            if src.startswith(s, i):
                toks.append(Tok('sym', s, line)); i += len(s); break
        else:
            for s in SYMS2:
                if src.startswith(s, i):
                    toks.append(Tok('sym', s, line)); i += len(s); break
            else:
                if c in '+-*/%^#<>=(){}[];:,.?|&@~':
                    toks.append(Tok('sym', c, line)); i += 1
                else:
                    raise ParseError(f'bad character {c!r} line {line}')
    toks.append(Tok('eof', '<eof>', line))
    return toks

BIN = {'or': (1, 1), 'and': (2, 2), '<': (3, 3), '>': (3, 3), '<=': (3, 3), '>=': (3, 3), '~=': (3, 3), '==': (3, 3),
       '..': (5, 4), '+': (6, 6), '-': (6, 6), '*': (7, 7), '/': (7, 7), '//': (7, 7), '%': (7, 7), '^': (10, 9)}
COMP = {'+=', '-=', '*=', '/=', '//=', '%=', '^=', '..='}

class Parser:
    def __init__(self, toks):
        self.t, self.p = toks, 0
    # -- helpers
    def pk(self, o=0):
        return self.t[min(self.p + o, len(self.t) - 1)]
    def nx(self):
        t = self.t[self.p]
        if t.t != 'eof': self.p += 1
        return t
    def is_(self, v, o=0):
        t = self.pk(o); return t.t in ('kw', 'sym') and t.v == v
    def eat(self, v):
        if self.is_(v): return self.nx()
        return None
    def need(self, v):
        if not self.is_(v): raise ParseError(f'expected {v!r} near line {self.pk().line} got {self.pk().v!r}')
        return self.nx()
    def name(self):
        t = self.pk()
        if t.t != 'id': raise ParseError(f'name expected line {t.line}')
        return self.nx().v
    # -- types (skipped)
    def skip_type(self):
        self.eat('|') or self.eat('&')
        self.skip_type_atom()
        while self.is_('?') or self.is_('|') or self.is_('&'):
            o = self.nx()
            if o.v != '?': self.skip_type_atom()
    def skip_balanced(self, open_, close):
        depth = 0
        while True:
            t = self.nx()
            if t.t == 'eof': raise ParseError('unbalanced type')
            if t.t == 'sym' and t.v == open_: depth += 1
            elif t.t == 'sym' and t.v == close:
                depth -= 1
                if depth == 0: return
    def skip_type_atom(self):
        t = self.pk()
        if self.is_('('):
            self.skip_balanced('(', ')')
            if self.eat('->'): self.skip_type()
        elif self.is_('<'):
            self.skip_balanced('<', '>'); self.skip_type_atom()
        elif self.is_('{'):
            self.skip_balanced('{', '}')
        elif t.t == 'str':
            self.nx()
        elif t.t == 'kw' and t.v in ('nil', 'true', 'false'):
            self.nx()
        elif t.t == 'id':
            self.nx()
            if t.v == 'typeof' and self.is_('('):
                self.skip_balanced('(', ')'); return
            while self.is_('.') and self.pk(1).t == 'id':
                self.nx(); self.nx()
            if self.is_('<'): self.skip_balanced('<', '>')
        else:
            raise ParseError(f'type expected line {t.line}')
    def generics(self):
        self.need('<')
        while not self.is_('>'): self.nx()
        self.need('>')
    # -- expressions
    def expr(self, lim=0):
        t = self.pk()
        if (t.t == 'kw' and t.v == 'not') or (t.t == 'sym' and t.v in ('-', '#')):
            self.nx(); l = ('un', t.v, self.expr(8))
        else:
            l = self.simple()
        while True:
            o = self.pk()
            b = BIN.get(o.v) if o.t in ('kw', 'sym') else None
            if not b or b[0] <= lim: break
            self.nx(); r = self.expr(b[1]); l = ('bin', o.v, l, r)
        return l
    def simple(self):
        t = self.pk()
        if t.t == 'num': self.nx(); e = ('num', t.v)
        elif t.t == 'str': self.nx(); e = ('str', t.v)
        elif t.t == 'istr': self.nx(); e = ('istr', t.v)
        elif t.t == 'kw' and t.v == 'nil': self.nx(); e = ('nil',)
        elif t.t == 'kw' and t.v in ('true', 'false'): self.nx(); e = ('bool', t.v == 'true')
        elif self.is_('...'): self.nx(); e = ('vararg',)
        elif self.is_('{'): e = self.table()
        elif self.is_('function'): self.nx(); e = self.funcbody(False)
        elif self.is_('if'): e = self.ifexpr()
        else: e = self.suffixed()
        while self.is_('::'):
            self.nx(); self.skip_type()
        return e
    def ifexpr(self):
        self.need('if'); c = self.expr(); self.need('then'); a = self.expr()
        while self.is_('elseif'):
            self.nx(); c2 = self.expr(); self.need('then'); a2 = self.expr()
            b = self.ifexpr_tail(); return ('ifexp', c, a, ('ifexp', c2, a2, b))
        self.need('else'); b = self.expr()
        return ('ifexp', c, a, b)
    def ifexpr_tail(self):
        if self.is_('elseif'):
            self.nx(); c = self.expr(); self.need('then'); a = self.expr()
            return ('ifexp', c, a, self.ifexpr_tail())
        self.need('else'); return self.expr()
    def table(self):
        self.need('{'); items = []
        while not self.is_('}'):
            if self.is_('['):
                self.nx(); k = self.expr(); self.need(']'); self.need('='); items.append(('idx', k, self.expr()))
            elif self.pk().t == 'id' and self.is_('=', 1):
                k = self.nx().v; self.nx(); items.append(('named', k, self.expr()))
            else:
                items.append(('arr', self.expr()))
            if not (self.eat(',') or self.eat(';')): break
        self.need('}')
        return ('table', items)
    def call_args(self):
        if self.is_('('):
            self.nx(); a = []
            if not self.is_(')'):
                a.append(self.expr())
                while self.eat(','): a.append(self.expr())
            self.need(')'); return a
        if self.pk().t in ('str', 'istr'):
            t = self.nx(); return [('str', t.v)]
        if self.is_('{'): return [self.table()]
        raise ParseError('call args expected')
    def suffixed(self):
        t = self.pk()
        if t.t == 'id': self.nx(); e = ('name', t.v)
        elif self.is_('('):
            self.nx(); x = self.expr(); self.need(')'); e = ('paren', x)
        else: raise ParseError(f'unexpected {t.v!r} line {t.line}')
        while True:
            c = self.pk()
            if self.is_('.'):
                self.nx(); e = ('index', e, ('str', self.name()))
            elif self.is_('['):
                self.nx(); k = self.expr(); self.need(']'); e = ('index', e, k)
            elif self.is_(':'):
                self.nx(); n = self.name(); e = ('mcall', e, n, self.call_args(), c.line)
            elif self.is_('(') or c.t in ('str', 'istr') or self.is_('{'):
                e = ('call', e, self.call_args(), c.line)
            else: break
        return e
    def funcbody(self, is_method):
        if self.is_('<'): self.generics()
        self.need('('); params = []; vararg = False
        if not self.is_(')'):
            while True:
                if self.is_('...'):
                    self.nx(); vararg = True
                    if self.eat(':'): self.skip_type()
                    break
                params.append(self.name())
                if self.eat(':'): self.skip_type()
                if not self.eat(','): break
        self.need(')')
        if self.eat(':'):
            if self.is_('('): self.skip_balanced('(', ')')
            else: self.skip_type()
        body = self.block(['end']); self.need('end')
        if is_method: params = ['self'] + params
        return ('func', params, vararg, body)
    # -- statements
    def at_end(self, terms):
        t = self.pk(); return t.t == 'eof' or (t.t == 'kw' and t.v in terms)
    def block(self, terms):
        out = []
        while not self.at_end(terms):
            t = self.pk()
            if t.t == 'kw' and t.v == 'return':
                self.nx(); vals = []; n = self.pk()
                if not (n.t == 'eof' or (n.t == 'kw' and n.v in ('end', 'else', 'elseif', 'until')) or self.is_(';')):
                    vals.append(self.expr())
                    while self.eat(','): vals.append(self.expr())
                self.eat(';'); out.append(('return', vals)); return out
            s = self.stat()
            if s: out.append(s)
        return out
    def stat(self):
        t = self.pk()
        if self.eat(';'): return None
        if self.is_('@'):
            self.nx(); self.name(); return self.stat()
        if t.t == 'kw':
            v = t.v
            if v == 'local':
                self.nx()
                if self.is_('function'):
                    self.nx(); n = self.name(); return ('localfunc', n, self.funcbody(False))
                names = []
                while True:
                    names.append(self.name())
                    if self.eat(':'): self.skip_type()
                    if not self.eat(','): break
                vals = []
                if self.eat('='):
                    vals.append(self.expr())
                    while self.eat(','): vals.append(self.expr())
                return ('local', names, vals, t.line)
            if v == 'function':
                self.nx(); target = ('name', self.name()); m = False
                while self.is_('.'):
                    self.nx(); target = ('index', target, ('str', self.name()))
                if self.is_(':'):
                    self.nx(); target = ('index', target, ('str', self.name())); m = True
                return ('assign', [target], [self.funcbody(m)], '=', t.line)
            if v == 'if':
                self.nx(); conds = [self.expr()]; self.need('then'); blocks = [self.block(['elseif', 'else', 'end'])]; els = None
                while self.is_('elseif'):
                    self.nx(); conds.append(self.expr()); self.need('then'); blocks.append(self.block(['elseif', 'else', 'end']))
                if self.eat('else'): els = self.block(['end'])
                self.need('end'); return ('if', conds, blocks, els)
            if v == 'while':
                self.nx(); c = self.expr(); self.need('do'); b = self.block(['end']); self.need('end'); return ('while', c, b)
            if v == 'for':
                self.nx(); n1 = self.name()
                if self.is_('='):
                    self.nx(); a = self.expr(); self.need(','); b = self.expr(); c = None
                    if self.eat(','): c = self.expr()
                    self.need('do'); body = self.block(['end']); self.need('end'); return ('numfor', n1, a, b, c, body)
                names = [n1]
                while self.eat(','): names.append(self.name())
                self.need('in'); exprs = [self.expr()]
                while self.eat(','): exprs.append(self.expr())
                self.need('do'); body = self.block(['end']); self.need('end'); return ('genfor', names, exprs, body)
            if v == 'repeat':
                self.nx(); b = self.block(['until']); self.need('until'); c = self.expr(); return ('repeat', b, c)
            if v == 'do':
                self.nx(); b = self.block(['end']); self.need('end'); return ('do', b)
            if v == 'break': self.nx(); return ('break',)
            raise ParseError(f'unexpected keyword {v} line {t.line}')
        if t.t == 'id':
            if t.v == 'continue' and self.pk(1).v not in ('=', '(', '.', ':', '[', ','):
                self.nx(); return ('continue',)
            if t.v == 'export' and self.pk(1).v == 'type':
                self.nx(); return self.typedecl()
            if t.v == 'type' and self.pk(1).t == 'id' and self.pk(2).v in ('=', '<'):
                return self.typedecl()
        e = self.suffixed()
        if self.is_('=') or self.is_(',') or (self.pk().t == 'sym' and self.pk().v in COMP):
            targets = [e]
            while self.eat(','): targets.append(self.suffixed())
            if self.pk().t == 'sym' and self.pk().v in COMP:
                op = self.nx().v; return ('assign', targets, [self.expr()], op, t.line)
            self.need('='); vals = [self.expr()]
            while self.eat(','): vals.append(self.expr())
            return ('assign', targets, vals, '=', t.line)
        return ('callstat', e, t.line)
    def typedecl(self):
        self.nx(); self.name()
        if self.is_('<'): self.generics()
        self.need('='); self.skip_type(); return None

def parse(src):
    toks = tokenize(src)
    p = Parser(toks)
    body = p.block([])
    if p.pk().t != 'eof': raise ParseError(f'trailing tokens near line {p.pk().line}')
    return body
