import json
import os
import sys
import unittest
from unittest.mock import patch
from io import BytesIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from external_luau_validator import (
    ExternalLuauValidator, EXTERNAL_VALIDATION_PASSED,
    EXTERNAL_VALIDATION_FAILED, EXTERNAL_VALIDATION_UNAVAILABLE,
    EXTERNAL_VALIDATION_INVALIDATED, invalidate_if_changed,
)

class FakeResponse:
    status = 200
    def __init__(self, payload): self.payload = json.dumps(payload).encode()
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self): return self.payload

class Level3Tests(unittest.TestCase):
    def test_valid_response(self):
        with patch("external_luau_validator.request.urlopen", return_value=FakeResponse({"valid": True, "errors": [], "warnings": [], "stats": {}})):
            r = ExternalLuauValidator().validate_exact("print('ok')")
        self.assertEqual(r["status"], EXTERNAL_VALIDATION_PASSED)
        self.assertEqual(r["evidence_status"], "ACTUAL_EXTERNAL_VALIDATION")

    def test_invalid_response(self):
        with patch("external_luau_validator.request.urlopen", return_value=FakeResponse({"valid": False, "errors": [{"line": 1, "col": 1, "message": "bad"}], "warnings": [], "stats": {}})):
            r = ExternalLuauValidator().validate_exact("local =")
        self.assertEqual(r["status"], EXTERNAL_VALIDATION_FAILED)
        self.assertEqual(r["errors_count"], 1)

    def test_mutation_invalidates(self):
        with patch("external_luau_validator.request.urlopen", return_value=FakeResponse({"valid": True, "errors": [], "warnings": [], "stats": {}})):
            r = ExternalLuauValidator().validate_exact("print('ok')")
        m = invalidate_if_changed(r, "print('changed')")
        self.assertEqual(m["status"], EXTERNAL_VALIDATION_INVALIDATED)

    def test_oversize_is_unavailable(self):
        r = ExternalLuauValidator().validate_exact("x" * 200_001)
        self.assertEqual(r["status"], EXTERNAL_VALIDATION_UNAVAILABLE)

    def test_malformed_json_is_unavailable(self):
        with patch("external_luau_validator.request.urlopen", return_value=FakeResponse.__new__(FakeResponse)) as p:
            p.return_value.status = 200
            p.return_value.__enter__ = lambda self: self
            p.return_value.__exit__ = lambda self, *args: None
            p.return_value.read = lambda: b"not json"
            r = ExternalLuauValidator().validate_exact("print('ok')")
        self.assertEqual(r["status"], EXTERNAL_VALIDATION_UNAVAILABLE)

if __name__ == "__main__":
    unittest.main()
