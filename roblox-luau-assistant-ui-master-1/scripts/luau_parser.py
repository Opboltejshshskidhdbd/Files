#!/usr/bin/env python3
"""Pure-Python Luau structural/syntax parser. Not the official Luau compiler."""
import re,sys
class LuauSyntaxError(Exception):
    def __init__(self,line,col,msg,hint=None): self.line=line; self.col=col; self.msg=msg; self.hint=hint
    def __str__(self): return f"{self.line}:{self.col}: {self.msg}"
class Tok:
    __slots__=('kind','value','line','col')
    def __init__(self,k,v,l,c): self.kind=k; self.value=v; self.line=l; self.col=c
KEY={'and','break','do','else','elseif','end','false','for','function','if','in','local','nil','not','or','repeat','return','then','true','until','while','continue'}
OPS=['...','..=','//=','+=','-=','*=','/=','%=','^=','..','==','~=','<=','>=','->','::','//']
SINGLE=set('+-*/%^#<>=(){}[];:,.&|?@')
def tokenize(src):
    out=[];i=0;line=1;ls=0;n=len(src)
    def err(msg): raise LuauSyntaxError(line,i-ls+1,msg)
    while i<n:
        c=src[i]
        if c=='\n': line+=1;i+=1;ls=i;continue
        if c.isspace(): i+=1;continue
        if src.startswith('--',i):
            m=re.match(r'--\[(=*)\[',src[i:])
            if m:
                close=']'+m.group(1)+']';j=src.find(close,i+len(m.group(0)))
                if j<0: err('unfinished long comment')
                line+=src.count('\n',i,j);k=src.rfind('\n',i,j);ls=k+1 if k>=0 else ls;i=j+len(close);continue
            j=src.find('\n',i);i=n if j<0 else j;continue
        if src.startswith('[',i):
            m=re.match(r'\[(=*)\[',src[i:])
            if m:
                close=']'+m.group(1)+']';j=src.find(close,i+len(m.group(0)))
                if j<0: err('unfinished long string')
                out.append(Tok('string',src[i:j+len(close)],line,i-ls+1));line+=src.count('\n',i,j);k=src.rfind('\n',i,j);ls=k+1 if k>=0 else ls;i=j+len(close);continue
        if c.isalpha() or c=='_':
            j=i+1
            while j<n and (src[j].isalnum() or src[j]=='_'): j+=1
            v=src[i:j];out.append(Tok('kw' if v in KEY else 'name',v,line,i-ls+1));i=j;continue
        if c.isdigit() or (c=='.' and i+1<n and src[i+1].isdigit()):
            m=re.match(r'(?:0[xX][0-9a-fA-F_]+|0[bB][01_]+|(?:\d[\d_]*\.?[\d_]*|\.\d[\d_]*)(?:[eE][+-]?\d+)?)',src[i:]);v=m.group(0);out.append(Tok('num',v,line,i-ls+1));i+=len(v);continue
        if c in "'\"":
            q=c;j=i+1
            while j<n and src[j]!=q:
                if src[j]=='\\': j+=2
                else:
                    if src[j]=='\n': err('unfinished string')
                    j+=1
            if j>=n: err('unfinished string')
            out.append(Tok('string',src[i:j+1],line,i-ls+1));i=j+1;continue
        if c=='`':
            j=i+1
            while j<n:
                if src[j]=='\\': j+=2;continue
                if src[j]=='`': break
                j+=1
            if j>=n: err('unfinished interpolated string')
            out.append(Tok('istring',src[i:j+1],line,i-ls+1));i=j+1;continue
        hit=next((op for op in OPS if src.startswith(op,i)),None)
        if hit: out.append(Tok('op',hit,line,i-ls+1));i+=len(hit);continue
        if c in SINGLE: out.append(Tok('op',c,line,i-ls+1));i+=1;continue
        err(f'unexpected symbol {c!r}')
    out.append(Tok('eof','<eof>',line,i-ls+1));return out
class Parser:
    def __init__(self,t): self.t=t;self.p=0;self.loops=0;self.varargs=[True];self.warnings=[]
    def peek(self,k=0): return self.t[min(self.p+k,len(self.t)-1)]
    def is_(self,v,k=0): return self.peek(k).value==v
    def next(self): x=self.peek();self.p+=x.kind!='eof';return x
    def fail(self,msg,t=None,hint=None):
        t=t or self.peek();raise LuauSyntaxError(t.line,t.col,msg,hint)
    def expect(self,v,hint=None):
        if self.is_(v): return self.next()
        self.fail(f"expected '{v}' near {'<eof>' if self.peek().kind=='eof' else repr(self.peek().value)}",hint=hint)
    def name(self):
        if self.peek().kind=='name': return self.next()
        self.fail('expected identifier')
    def block_end(self): return self.peek().kind=='eof' or self.peek().value in ('end','else','elseif','until')
    def chunk(self): self.block();
    def block(self):
        while not self.block_end():
            if self.is_('return'):
                self.next()
                if not self.block_end() and not self.is_(';'): self.exprlist()
                self.next() if self.is_(';') else None
                if not self.block_end(): self.fail("'return' must be the last statement in its block")
                return
            self.stat(); self.next() if self.is_(';') else None
    def stat(self):
        v=self.peek().value
        if v=='if': self.ifstat();return
        if v=='while': self.next();self.expr();self.expect('do');self.loops+=1;self.block();self.loops-=1;self.expect('end');return
        if v=='repeat': self.next();self.loops+=1;self.block();self.loops-=1;self.expect('until');self.expr();return
        if v=='do': self.next();self.block();self.expect('end');return
        if v=='for': self.forstat();return
        if v=='function':
            self.next();self.name()
            while self.is_('.'):self.next();self.name()
            if self.is_(':'):self.next();self.name()
            self.funcbody();return
        if v=='local':
            self.next()
            if self.is_('function'): self.next();self.name();self.funcbody();return
            self.name()
            if self.is_(':'): self.next(); self.typex()
            while self.is_(','): self.next();self.name()
            if self.is_('='): self.next();self.exprlist()
            return
        if v in ('break','continue'):
            x=self.next()
            if self.loops==0:self.fail(f"'{x.value}' used outside of a loop",x)
            return
        if v in ('end','else','elseif','until','then','in'): self.fail(f"unexpected '{v}'")
        if v=='export' and self.is_('type',1): self.next();self.typealias();return
        if v=='type' and self.peek(1).kind=='name': self.typealias();return
        self.exprstat()
    def ifstat(self):
        self.next();self.expr();self.expect('then');self.block()
        while self.is_('elseif'): self.next();self.expr();self.expect('then');self.block()
        if self.is_('else'): self.next();self.block()
        self.expect('end')
    def forstat(self):
        self.next();self.name()
        if self.is_('='):
            self.next();self.expr();self.expect(',');self.expr();
            if self.is_(','):self.next();self.expr()
        else:
            while self.is_(','):self.next();self.name()
            self.expect('in');self.exprlist()
        self.expect('do');self.loops+=1;self.block();self.loops-=1;self.expect('end')
    def funcbody(self):
        if self.is_('<'): self.generics()
        self.expect('(');va=False
        if not self.is_(')'):
            while True:
                if self.is_('...'):self.next();va=True;break
                self.name()
                if self.is_(':'):self.next();self.typex()
                if not self.is_(','):break
                self.next()
        self.expect(')')
        if self.is_(':'):self.next();self.typex()
        old=self.varargs;self.varargs=old+[va];self.block();self.varargs=old;self.expect('end')
    def generics(self):
        self.expect('<');self.name()
        while self.is_(','):self.next();self.name()
        self.expect('>')
    def typealias(self):
        self.next();self.name();
        if self.is_('<'):self.generics()
        self.expect('=');self.typex()
    def typex(self):
        if self.is_('|') or self.is_('&'):self.next()
        self.typesimple()
        while self.is_('?') or self.is_('|') or self.is_('&'):
            self.next()
            if self.peek().value not in (')','}',',',';','=','>') and self.peek().kind!='eof' and not self.block_end():
                if self.peek().kind in ('name','string','num') or self.peek().value in ('{','(','nil','typeof'):
                    self.typesimple()
    def typesimple(self):
        if self.is_('typeof') and self.is_('(',1):
            self.next();self.next();self.expr();self.expect(')');return
        if self.is_('{'):
            self.next()
            while not self.is_('}'):
                if self.peek().kind=='name' and self.is_(':',1): self.next(); self.next(); self.typex()
                elif self.is_('['): self.next(); self.typex(); self.expect(']'); self.expect(':'); self.typex()
                else: self.typex()
                self.next() if self.is_(',') or self.is_(';') else None
            self.expect('}');return
        if self.is_('('):
            self.next()
            def one():
                if self.peek().kind=='name' and self.is_(':',1):self.next();self.next()
                if self.is_('...'):self.next()
                self.typex()
            if not self.is_(')'):
                one()
                while self.is_(','):self.next();one()
            self.expect(')');
            if self.is_('->'):self.next();self.typex()
            return
        if self.peek().kind in ('name','string','num') or self.is_('nil'):
            self.next()
            while self.is_('.') and self.peek(1).kind=='name':self.next();self.next()
            if self.is_('<'):
                self.next(); self.typex()
                while self.is_(','): self.next(); self.typex()
                self.expect('>')
            return
        self.fail('expected a type')
    def exprlist(self):
        self.expr()
        while self.is_(','):self.next();self.expr()
    def expr(self,limit=0):
        if self.peek().value in ('not','-','#'):self.next();self.expr(8)
        else:self.simple()
        pri={'or':1,'and':2,'==':3,'~=':3,'<':3,'>':3,'<=':3,'>=':3,'..':5,'+':6,'-':6,'*':7,'/':7,'//':7,'%':7,'^':9}
        while self.peek().value in pri and pri[self.peek().value]>limit:
            p=pri[self.next().value];self.expr(p)
    def simple(self):
        x=self.peek()
        if x.kind in ('num','string','istring') or x.value in ('nil','true','false'):self.next()
        elif x.value=='...':
            self.next()
            if not self.varargs[-1]:self.fail("cannot use '...' outside of a vararg function",x)
        elif x.value=='function':self.next();self.funcbody()
        elif x.value=='if':self.ifexpr()
        elif x.value=='{':self.table()
        else:self.suffixed()
        while self.is_('::'):self.next();self.typex()
    def ifexpr(self):
        self.next();self.expr();self.expect('then');self.expr()
        while self.is_('elseif'):self.next();self.expr();self.expect('then');self.expr()
        self.expect('else');self.expr()
    def suffixed(self):
        if self.is_('('):
            self.next();self.expr();self.expect(')');kind='paren'
        elif self.peek().kind=='name':
            self.next();kind='var'
        else:self.fail('expected expression')
        while True:
            if self.is_('.'):
                self.next();self.name();kind='var'
            elif self.is_('['):self.next();self.expr();self.expect(']');kind='var'
            elif self.is_(':'):
                self.next();self.name();self.callargs();kind='call'
            elif self.is_('(') or self.peek().kind in ('string','istring') or self.is_('{'):
                self.callargs();kind='call'
            else:return kind
    def callargs(self):
        if self.peek().kind in ('string','istring'):self.next();return
        if self.is_('{'):self.table();return
        self.expect('(')
        if not self.is_(')'):self.exprlist()
        self.expect(')')
    def table(self):
        self.expect('{')
        while not self.is_('}'):
            if self.is_('['):self.next();self.expr();self.expect(']');self.expect('=');self.expr()
            elif self.peek().kind=='name' and self.is_('=',1):self.next();self.next();self.expr()
            else:self.expr()
            if self.is_(',') or self.is_(';'):self.next()
            elif not self.is_('}'):self.fail("expected ',' or '}' in table")
        self.next()
    def exprstat(self):
        k=self.suffixed()
        if self.is_('=') or self.is_(','):
            if k!='var':self.fail('cannot assign to this expression')
            while self.is_(','):self.next();self.suffixed()
            self.expect('=');self.exprlist();return
        if self.peek().value in ('+=','-=','*=','/=','%=','^=','..=','//='):
            if k!='var':self.fail('cannot assign to this expression')
            self.next();self.expr();return
        if k!='call':self.fail('syntax error: expression is not a statement')
def check(source):
    try:
        p=Parser(tokenize(source));p.chunk();
        if p.peek().kind!='eof':p.fail(f"unexpected '{p.peek().value}'")
        return {'ok':True,'error':None,'hint':None,'line':None,'warnings':p.warnings}
    except LuauSyntaxError as e:return {'ok':False,'error':f'{e.line}:{e.col}: {e.msg}','hint':e.hint,'line':e.line,'warnings':[]}
def main():
    src=open(sys.argv[1],encoding='utf-8').read() if len(sys.argv)>1 else sys.stdin.read();r=check(src)
    if r['ok']: print('SYNTAX OK (parsed fully; this is not a type check or a runtime test)');return 0
    print('SYNTAX ERROR',r['error']);
    if r['hint']:print('hint:',r['hint'])
    return 1
if __name__=='__main__':sys.exit(main())
