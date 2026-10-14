#!/usr/bin/env python3
import argparse,json,pathlib,sys
from luau_syntax import validate_luau_files
p=argparse.ArgumentParser();p.add_argument("files",nargs="+");a=p.parse_args();files={str(pathlib.Path(f)):pathlib.Path(f).read_text(encoding="utf-8") for f in a.files};r=validate_luau_files(files);print(json.dumps(r,indent=2));sys.exit(0 if r["status"]=="SYNTAX_VERIFIED" else 1)
