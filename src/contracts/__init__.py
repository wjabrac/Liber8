"""Public API for LIBR8 contracts."""

from .errors import ValidationError
from .models import (
    TagSet,
    QueryPlan,
    MemoryBlock,
    WritebackPackage,
    EventRecord,
    _now_iso
)
from .validators import (
    validate_tagset,
    validate_queryplan,
    validate_memoryblock,
    validate_writeback,
    validate_eventrecord,
    _ensure_jsonable,
    _require
)
from .serializers import (
    tagset_to_dict, tagset_from_dict,
    queryplan_to_dict, queryplan_from_dict,
    memoryblock_to_dict, memoryblock_from_dict,
    writeback_to_dict, writeback_from_dict,
    eventrecord_to_dict, eventrecord_from_dict
)

# Monkey-patch models with exactly the same to_dict/from_dict interface as before 
# so we don't break existing callers doing `event.to_dict()` or `EventRecord.from_dict()`.
TagSet.to_dict = tagset_to_dict
TagSet.from_dict = classmethod(lambda cls, d: tagset_from_dict(d))
QueryPlan.to_dict = queryplan_to_dict
QueryPlan.from_dict = classmethod(lambda cls, d: queryplan_from_dict(d))
MemoryBlock.to_dict = memoryblock_to_dict
MemoryBlock.from_dict = classmethod(lambda cls, d: memoryblock_from_dict(d))
WritebackPackage.to_dict = writeback_to_dict
WritebackPackage.from_dict = classmethod(lambda cls, d: writeback_from_dict(d))
EventRecord.to_dict = eventrecord_to_dict
EventRecord.from_dict = classmethod(lambda cls, d: eventrecord_from_dict(d))

__all__ = [
    "ValidationError",
    "TagSet",
    "QueryPlan",
    "MemoryBlock",
    "WritebackPackage",
    "EventRecord",
    "validate_tagset",
    "validate_queryplan",
    "validate_memoryblock",
    "validate_writeback",
    "validate_eventrecord",
    "_now_iso",
    "_ensure_jsonable",
    "_require"
]
