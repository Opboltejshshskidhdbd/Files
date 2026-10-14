# Validator Bridge Contract — Level 3 External Luau

## Required callable operation
`validate_luau_source(source, source_name, source_hash)`

## Required behavior
1. Verify the supplied hash against the exact source bytes.
2. Reject or report hash mismatch without claiming validation.
3. POST exactly `{ "code": source }` to:
   `https://luau-validator.oboltr895.workers.dev/validate`
4. Do not reformat, minify, strip comments, or repair source before the first request.
5. Return the API response without fabricating diagnostics.
6. Attach Dev Master metadata: endpoint, source hash, attempt, timestamp, status, source-truth status, evidence status.
7. Map transport/schema/size failures to `EXTERNAL_VALIDATION_UNAVAILABLE`.
8. Map API `valid:false` to `EXTERNAL_VALIDATION_FAILED`.
9. Map API `valid:true` to `EXTERNAL_VALIDATION_PASSED` only when the request actually succeeded.
10. If the source later changes, mark the prior result `EXTERNAL_VALIDATION_INVALIDATED`.

## Repair boundary
The bridge validates; it does not silently edit source. The Engineering Gate owns root-cause analysis and actual repair, followed by Level 1/2/3 revalidation.

## Host truth
A documented bridge contract is not an implementation. The current package has a Python HTTP client, but ordinary ChatGPT plugin generation cannot claim host execution until an approved callable host action is actually available.
