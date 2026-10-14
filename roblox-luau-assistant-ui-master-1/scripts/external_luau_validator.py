"""Level 3 external Luau validator client.

This module sends the exact UTF-8 source in a JSON POST body to the configured
external service. It never repairs or reformats source before the first call.
It is an integration component; packaging this file does not by itself create
a callable host/network tool inside ChatGPT.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
import json
import time
from typing import Any, Callable, Mapping
from urllib import error, request

ENDPOINT = "https://luau-validator.oboltr895.workers.dev/validate"
VALIDATOR = "external-luau-validator"
MAX_SOURCE_BYTES = 200_000
DEFAULT_TIMEOUT_SECONDS = 15.0
MAX_REPAIR_ATTEMPTS = 3

EXTERNAL_VALIDATION_PASSED = "EXTERNAL_VALIDATION_PASSED"
EXTERNAL_VALIDATION_FAILED = "EXTERNAL_VALIDATION_FAILED"
EXTERNAL_VALIDATION_UNAVAILABLE = "EXTERNAL_VALIDATION_UNAVAILABLE"
EXTERNAL_VALIDATION_INVALIDATED = "EXTERNAL_VALIDATION_INVALIDATED"


def source_hash(source: str) -> str:
    return sha256(source.encode("utf-8")).hexdigest()


def source_size_bytes(source: str) -> int:
    return len(source.encode("utf-8"))


def _diagnostics(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for key in ("errors", "warnings"):
        values = payload.get(key, [])
        if not isinstance(values, list):
            continue
        for item in values:
            if isinstance(item, dict):
                d = dict(item)
                d["_source"] = "api"
                d["_bucket"] = key
                out.append(d)
            else:
                out.append({"message": str(item), "_source": "api", "_bucket": key})
    return out


@dataclass
class ValidationReceipt:
    validation_level: int
    validator: str
    endpoint: str
    source_hash: str
    source_bytes: int
    attempt: int
    status: str
    errors_count: int
    warnings_count: int
    diagnostics: list[dict[str, Any]]
    timestamp: float
    source_truth_status: str
    evidence_status: str
    api_http_status: int | None = None
    api_response: dict[str, Any] | None = None
    failure_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExternalLuauValidator:
    def __init__(self, endpoint: str = ENDPOINT, timeout: float = DEFAULT_TIMEOUT_SECONDS):
        self.endpoint = endpoint
        self.timeout = timeout

    def validate_exact(self, source: str, source_name: str = "<source>", attempt: int = 1) -> dict[str, Any]:
        frozen_hash = source_hash(source)
        size = source_size_bytes(source)
        if size > MAX_SOURCE_BYTES:
            return ValidationReceipt(
                3, VALIDATOR, self.endpoint, frozen_hash, size, attempt,
                EXTERNAL_VALIDATION_UNAVAILABLE, 0, 0,
                [{"_source": "dev-master", "_bucket": "transport", "rule": "MAX_SOURCE_BYTES",
                  "message": f"Source exceeds supported 200KB limit: {size} bytes."}],
                time.time(), "CONFIRMED", "EXTERNAL_VALIDATION_UNAVAILABLE",
                failure_reason="SOURCE_TOO_LARGE"
            ).to_dict()

        # Exact source boundary: JSON encoding is the transport wrapper; the
        # code string itself is unchanged UTF-8 source.
        body = json.dumps({"code": source}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        req = request.Request(
            self.endpoint,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                http_status = getattr(response, "status", None)
                raw = response.read()
        except error.HTTPError as exc:
            return ValidationReceipt(
                3, VALIDATOR, self.endpoint, frozen_hash, size, attempt,
                EXTERNAL_VALIDATION_UNAVAILABLE, 0, 0,
                [{"_source": "dev-master", "_bucket": "transport", "message": f"HTTP {exc.code}"}],
                time.time(), "CONFIRMED", "EXTERNAL_VALIDATION_UNAVAILABLE",
                api_http_status=exc.code, failure_reason="HTTP_FAILURE"
            ).to_dict()
        except (error.URLError, TimeoutError, OSError) as exc:
            return ValidationReceipt(
                3, VALIDATOR, self.endpoint, frozen_hash, size, attempt,
                EXTERNAL_VALIDATION_UNAVAILABLE, 0, 0,
                [{"_source": "dev-master", "_bucket": "transport", "message": str(exc)}],
                time.time(), "CONFIRMED", "EXTERNAL_VALIDATION_UNAVAILABLE",
                failure_reason="NETWORK_OR_TIMEOUT"
            ).to_dict()

        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return ValidationReceipt(
                3, VALIDATOR, self.endpoint, frozen_hash, size, attempt,
                EXTERNAL_VALIDATION_UNAVAILABLE, 0, 0,
                [{"_source": "dev-master", "_bucket": "transport", "message": str(exc)}],
                time.time(), "CONFIRMED", "EXTERNAL_VALIDATION_UNAVAILABLE",
                api_http_status=http_status, failure_reason="MALFORMED_JSON"
            ).to_dict()

        if not isinstance(payload, dict) or not isinstance(payload.get("valid"), bool):
            return ValidationReceipt(
                3, VALIDATOR, self.endpoint, frozen_hash, size, attempt,
                EXTERNAL_VALIDATION_UNAVAILABLE, 0, 0,
                [{"_source": "dev-master", "_bucket": "transport", "message": "Response missing boolean 'valid'."}],
                time.time(), "CONFIRMED", "EXTERNAL_VALIDATION_UNAVAILABLE",
                api_http_status=http_status, failure_reason="INVALID_RESPONSE_SCHEMA"
            ).to_dict()

        errors = payload.get("errors", []) if isinstance(payload.get("errors", []), list) else []
        warnings = payload.get("warnings", []) if isinstance(payload.get("warnings", []), list) else []
        diagnostics = _diagnostics(payload)
        status = EXTERNAL_VALIDATION_PASSED if payload["valid"] else EXTERNAL_VALIDATION_FAILED
        receipt = ValidationReceipt(
            3, VALIDATOR, self.endpoint, frozen_hash, size, attempt, status,
            len(errors), len(warnings), diagnostics, time.time(), "CONFIRMED",
            "ACTUAL_EXTERNAL_VALIDATION", api_http_status=http_status,
            api_response=payload,
        ).to_dict()
        receipt["source_name"] = source_name
        receipt["api_returned_fields"] = sorted(payload.keys())
        return receipt


def invalidate_if_changed(receipt: Mapping[str, Any], current_source: str) -> dict[str, Any]:
    current_hash = source_hash(current_source)
    if current_hash != receipt.get("source_hash") and receipt.get("status") in {
        EXTERNAL_VALIDATION_PASSED, EXTERNAL_VALIDATION_FAILED
    }:
        out = dict(receipt)
        out["status"] = EXTERNAL_VALIDATION_INVALIDATED
        out["source_truth_status"] = "MISMATCH"
        out["invalidated_by_hash"] = current_hash
        out["evidence_status"] = "EXTERNAL_VALIDATION_INVALIDATED"
        return out
    return dict(receipt)


def validate_after_repairs(
    source_provider: Callable[[], str],
    source_name: str = "<source>",
    repair: Callable[[str, dict[str, Any]], str] | None = None,
    max_attempts: int = MAX_REPAIR_ATTEMPTS,
    validator: ExternalLuauValidator | None = None,
) -> dict[str, Any]:
    """Run Level 3 with an explicit actual-source repair callback.

    The callback is responsible for changing the real current source. This
    module never treats an explanation as a repair and never edits source itself.
    """
    client = validator or ExternalLuauValidator()
    history: list[dict[str, Any]] = []
    for attempt in range(1, max_attempts + 1):
        source = source_provider()
        result = client.validate_exact(source, source_name, attempt)
        history.append(result)
        if result["status"] == EXTERNAL_VALIDATION_PASSED:
            return {"status": result["status"], "attempts": history}
        if result["status"] == EXTERNAL_VALIDATION_UNAVAILABLE:
            return {"status": result["status"], "attempts": history}
        if repair is None or attempt >= max_attempts:
            return {"status": "NOT_VERIFIED", "attempts": history}
        updated = repair(source, result)
        if not isinstance(updated, str) or updated == source:
            return {"status": "NOT_VERIFIED", "attempts": history, "repair_status": "ACTUAL_SOURCE_NOT_CHANGED"}
    return {"status": "NOT_VERIFIED", "attempts": history}
