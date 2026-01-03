# failure_classes_v0.md

## Failure Classes v0
- `validation_error`: Contract or schema validation failed.
- `backend_unavailable`: Model endpoint or memory store unavailable.
- `timeout`: Operation exceeded allotted time.
- `unknown`: Catch-all for uncategorized failures.

## Usage
- `EventRecord.failure_class` is optional and should be set when `outcome` is non-success.
