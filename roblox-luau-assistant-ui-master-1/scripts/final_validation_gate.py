"""Exact-source validation gate. Never executes Roblox game code."""
from __future__ import annotations
from hashlib import sha256
try:
    from .luau_syntax import validate_luau_files
except ImportError:
    from luau_syntax import validate_luau_files

def canonical_hash(files):
    return sha256(''.join(name+'\0'+files[name] for name in sorted(files)).encode()).hexdigest()

def validate_exact(files):
    frozen={k:v for k,v in files.items()}
    checked=validate_luau_files(frozen)
    checked_hash=canonical_hash(frozen)
    return checked, checked_hash

def delivery_gate(files, delivered_files=None):
    checked, checked_hash=validate_exact(files)
    delivered=files if delivered_files is None else delivered_files
    delivered_hash=canonical_hash(delivered)
    if checked_hash != delivered_hash:
        return {'status':'VALIDATION_INVALIDATED','checked_hash':checked_hash,'delivered_hash':delivered_hash,'validation':checked}
    return {'status':checked['status'],'checked_hash':checked_hash,'delivered_hash':delivered_hash,'validation':checked}
