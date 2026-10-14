"""Luau syntax validation API backed by the bundled recursive parser.
Not the official Luau compiler, type checker, or runtime."""
from dataclasses import dataclass,asdict
from hashlib import sha256
from time import perf_counter
import re
try:
 from .luau_parser import check as _check
except ImportError:
 from luau_parser import check as _check
VALIDATOR='Roblox Dev Master Luau parser (Python, not the official compiler)';VERSION='2.0.0'
@dataclass
class Diagnostic:
 file:str;line:int;column:int;severity:str;message:str;category:str;hint:str=''
 def to_dict(self):return asdict(self)
class Result(dict):
 """dict result that also supports .to_dict() and attribute access (backward compatible)."""
 def to_dict(self):return dict(self)
 def __getattr__(self,k):
  try:return self[k]
  except KeyError:raise AttributeError(k)
def validate_source(source,file='<source>'):
 t=perf_counter();r=_check(source);ds=[]
 if not r['ok']:
  m=re.match(r'^(\d+):(\d+): (.*)$',r['error'] or '')
  ds.append(Diagnostic(file,int(m.group(1)) if m else 0,int(m.group(2)) if m else 0,'error',m.group(3) if m else r['error'],'syntax',r.get('hint') or '').to_dict())
 for w in r.get('warnings',[]):
  ds.append(Diagnostic(file,0,0,'warning',str(w),'style').to_dict())
 e=sum(d['severity']=='error' for d in ds)
 return Result({'status':'SYNTAX_FAILED' if e else 'SYNTAX_VERIFIED','validator':VALIDATOR,'validator_version':VERSION,'source_hash':sha256(source.encode()).hexdigest(),'files_checked':[file],'diagnostics':ds,'error_count':e,'warning_count':len(ds)-e,'execution_time':perf_counter()-t})
def validate_luau_source(source,file='<source>'):return validate_source(source,file)
def validate_luau_files(files):
 rs=[validate_source(s,n) for n,s in files.items()];ds=[d for r in rs for d in r['diagnostics']];e=sum(d['severity']=='error' for d in ds)
 canonical=''.join(n+'\0'+files[n] for n in sorted(files))
 return {'status':'SYNTAX_FAILED' if e else 'SYNTAX_VERIFIED','validator':VALIDATOR,'validator_version':VERSION,'source_hash':sha256(canonical.encode()).hexdigest(),'files_checked':list(files),'diagnostics':ds,'error_count':e,'warning_count':len(ds)-e,'execution_time':sum(r['execution_time'] for r in rs)}
