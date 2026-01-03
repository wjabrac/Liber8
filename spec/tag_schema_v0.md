# tag_schema_v0.md

## Versioning
- schema_version: "v0"

## Required Keys
- None required in v0 (allow incremental adoption).

## Allowed Values
- Free-form string keys with JSON-serializable values.

## Numeric Ranges
- Uncertainty values must be floats between 0 and 1.

## Uncertainty Representation
- `TagSet.uncertainty` maps tag keys to confidence values in [0, 1].

## Migration Notes
- Future versions may enforce required keys and controlled vocabularies.
