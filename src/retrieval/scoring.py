"""Retrieval scoring based on tag overlaps and penalties, per spec/retrieval_scoring_v0_1.md."""

import math
from datetime import datetime, timezone
from typing import Any, Dict

from src.contracts import MemoryBlock, QueryPlan, TagSet


def calculate_tag_overlap(query_tags: TagSet, block_tags: TagSet) -> float:
    """Calculates a simple Jaccard index overlap for the tags."""
    q_keys = set(query_tags.tags.keys())
    b_keys = set(block_tags.tags.keys())
    intersection = q_keys.intersection(b_keys)
    union = q_keys.union(b_keys)
    if not union:
        return 0.0
    return len(intersection) / len(union)


def calculate_recency(updated_at: str) -> float:
    """Calculates recency decay score."""
    try:
        updated = datetime.fromisoformat(updated_at)
        now = datetime.now(timezone.utc)
        delta_days = (now - updated).total_seconds() / 86400.0
        # simple exponential decay: older records get lower score
        return math.exp(-0.1 * max(0.0, delta_days))
    except Exception:
        return 0.5


def score_block(block: MemoryBlock, query_tags: TagSet, plan: QueryPlan) -> Dict[str, Any]:
    """
    Scores a memory block against query tags based on tag overlap,
    recency, lane bonuses, and penalties (like expired TTL or low confidence).
    """
    # 1. Penalty for expired TTL
    if block.valid_until:
        try:
            valid_until = datetime.fromisoformat(block.valid_until)
            if valid_until < datetime.now(timezone.utc):
                return {"total": 0.0, "components": {"penalized": "expired"}, "matched_tags": []}
        except Exception:
            pass
            
    # 2. Penalty for low confidence
    if block.confidence < 0.2:
        return {"total": 0.0, "components": {"penalized": "low_confidence"}, "matched_tags": []}
        
    tag_overlap = calculate_tag_overlap(query_tags, block.tags)
    recency = calculate_recency(block.updated_at)
    
    # 3. Simple static bonuses
    lane_bonus = 0.2 if block.lane in ["semantic", "procedural"] else 0.0
    provenance_bonus = 0.1 if "trusted" in block.provenance else 0.0
    
    # 4. Blend using QueryPlan configuration scoring_knobs
    w_fresh = plan.scoring_knobs.get("freshness", 0.3)
    w_tag = plan.scoring_knobs.get("relevance", 0.7)
    
    total = (tag_overlap * float(w_tag)) + (recency * float(w_fresh)) + lane_bonus + provenance_bonus
    # Clamp final score
    total = min(1.0, max(0.0, total))
    
    matched_tags = list(set(query_tags.tags.keys()).intersection(set(block.tags.tags.keys())))
    
    return {
        "total": total,
        "components": {
            "tag_overlap": tag_overlap,
            "recency": recency,
            "lane_bonus": lane_bonus,
            "provenance_bonus": provenance_bonus
        },
        "matched_tags": matched_tags
    }
