"""Level 3 integration helpers; Level 1/2 remain separate gates."""
from __future__ import annotations
from typing import Mapping
from external_luau_validator import ExternalLuauValidator, invalidate_if_changed

VALIDATION_LADDER = (
    "LEVEL_1_ENGINEERING_SELF_AUDIT",
    "LEVEL_2_BUNDLED_LUAU_PARSER",
    "LEVEL_3_EXTERNAL_LUAU_VALIDATOR",
    "ROBLOX_API_TRUTH_GATE",
    "WHOLE_SOURCE_DEFECT_EXHAUSTION",
    "REPAIR_REVALIDATION",
    "SECOND_PASS_FALSIFICATION",
    "FINAL_EVIDENCE",
)

def validate_file(source: str, source_name: str = "<source>", attempt: int = 1, client: ExternalLuauValidator | None = None) -> dict:
    return (client or ExternalLuauValidator()).validate_exact(source, source_name, attempt)

def validate_files(files: Mapping[str, str], client: ExternalLuauValidator | None = None) -> dict:
    client = client or ExternalLuauValidator()
    results = {name: client.validate_exact(source, name, 1) for name, source in files.items()}
    return {"validation_level": 3, "files": results, "all_passed": all(r["status"] == "EXTERNAL_VALIDATION_PASSED" for r in results.values())}

def revalidate_current(receipt: dict, current_source: str, client: ExternalLuauValidator | None = None) -> dict:
    checked = invalidate_if_changed(receipt, current_source)
    if checked["status"] == "EXTERNAL_VALIDATION_INVALIDATED":
        return {"previous": checked, "current": (client or ExternalLuauValidator()).validate_exact(current_source)}
    return {"previous": checked}
