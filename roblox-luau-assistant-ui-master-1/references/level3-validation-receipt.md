# Level 3 Validation Receipt Contract

Minimum generated metadata:
- `validation_level`
- `validator`
- `endpoint`
- `source_hash`
- `attempt`
- `status`
- `errors_count`
- `warnings_count`
- `diagnostics`
- `timestamp`
- `source_truth_status`
- `evidence_status`

API-returned payload fields must remain distinguishable from Dev Master-generated metadata.

Example status values:
- `EXTERNAL_VALIDATION_PASSED`
- `EXTERNAL_VALIDATION_FAILED`
- `EXTERNAL_VALIDATION_UNAVAILABLE`
- `EXTERNAL_VALIDATION_INVALIDATED`
- `NOT_VERIFIED`
