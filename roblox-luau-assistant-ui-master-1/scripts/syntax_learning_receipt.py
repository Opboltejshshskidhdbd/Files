"""Build a privacy-safe syntax learning receipt from explicit evidence."""
from __future__ import annotations
import json, re
from dataclasses import dataclass, asdict

PRIVATE_PATTERNS = [re.compile(r'(?i)twopartygamer'), re.compile(r'(?i)place\s*id'), re.compile(r'(?i)api[_-]?key'), re.compile(r'(?i)password|token|secret')]

@dataclass
class Receipt:
    failure_class: str
    root_cause: str
    actual_repair: str
    source_truth_confirmation: str
    validation_result: str
    regression_status: str
    generalization: str
    prevention_rule: str
    evidence_status: str
    reusable: bool

def sanitize(text: str) -> str:
    out = text
    for p in PRIVATE_PATTERNS:
        out = p.sub('[REDACTED]', out)
    return out

def make_receipt(**kwargs):
    required = ['failure_class','root_cause','actual_repair','source_truth_confirmation','validation_result','regression_status','generalization','prevention_rule','evidence_status','reusable']
    missing=[k for k in required if k not in kwargs]
    if missing: raise ValueError('missing receipt fields: '+', '.join(missing))
    r=Receipt(**{k:sanitize(str(kwargs[k])) if k!='reusable' else bool(kwargs[k]) for k in required})
    return asdict(r)

if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--failure-class',required=True); p.add_argument('--root-cause',required=True); p.add_argument('--actual-repair',required=True); p.add_argument('--source-truth-confirmation',required=True); p.add_argument('--validation-result',required=True); p.add_argument('--regression-status',required=True); p.add_argument('--generalization',required=True); p.add_argument('--prevention-rule',required=True); p.add_argument('--evidence-status',required=True); p.add_argument('--reusable',action='store_true')
    a=p.parse_args(); print(json.dumps(make_receipt(**vars(a)),indent=2))
