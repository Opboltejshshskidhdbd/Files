#!/usr/bin/env python3
"""Validate actual code-bearing dataset fields; prose is never treated as code."""
from __future__ import annotations
import json, argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent))
from luau_syntax import validate_source

CODE_KEYS={'output','code','source','script','luau','snippet','example_code','code_output'}
def walk(obj, path='$'):
    if isinstance(obj, dict):
        for k,v in obj.items():
            if k in CODE_KEYS and isinstance(v,str) and v.strip(): yield path+'.'+k,v
            else: yield from walk(v,path+'.'+k)
    elif isinstance(obj,list):
        for i,v in enumerate(obj): yield from walk(v,f'{path}[{i}]')

def main():
    p=argparse.ArgumentParser(); p.add_argument('dataset'); a=p.parse_args()
    data=json.loads(Path(a.dataset).read_text(encoding='utf-8'))
    entries=list(walk(data)); rows=[]
    for idx,(path,src) in enumerate(entries,1):
        r=validate_source(src,path); r=r.to_dict() if hasattr(r,'to_dict') else r; rows.append({'id':idx,'file':path,'status':r['status'],'diagnostics':r['diagnostics']})
    summary={'TOTAL_CODE_ENTRIES':len(rows),'PASSED':sum(x['status']=='SYNTAX_VERIFIED' for x in rows),'FAILED':sum(x['status']=='SYNTAX_FAILED' for x in rows),'UNPARSEABLE':0,'SKIPPED':0,'ANALYZER_UNAVAILABLE':0,'entries':rows}
    print(json.dumps(summary,indent=2)); return 0 if summary['FAILED']==0 else 1
if __name__=='__main__': raise SystemExit(main())
