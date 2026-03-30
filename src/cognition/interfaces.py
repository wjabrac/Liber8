"""Cognition and memory interfaces for LIBR8 backends."""

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
from src.contracts import TagSet, QueryPlan, MemoryBlock, WritebackPackage

class TagExtractor(ABC):
    @abstractmethod
    def extract(self, task: str) -> TagSet:
        pass

class QueryPlanner(ABC):
    @abstractmethod
    def plan(self, tags: TagSet) -> QueryPlan:
        pass

class RouterPolicyProvider(ABC):
    @abstractmethod
    def route(self, task: str, tags: TagSet, query_plan: QueryPlan, retrieved: List[MemoryBlock]) -> Tuple[List[str], str, List[Dict[str, Any]], float]:
        """Returns agents, routing_reason, decomposition, confidence"""
        pass

class Synthesizer(ABC):
    @abstractmethod
    def synthesize(self, task: str, tags: TagSet, retrieved: List[MemoryBlock], tool_results: List[Dict[str, Any]]) -> str:
        """Returns the synthesis episode content"""
        pass

class Evaluator(ABC):
    @abstractmethod
    def evaluate(self, task: str, synthesis: str, tags: TagSet) -> WritebackPackage:
        pass

class MemoryStore(ABC):
    @abstractmethod
    def read(self, tags: TagSet, plan: QueryPlan) -> List[MemoryBlock]:
        pass

    @abstractmethod
    def write(self, block: MemoryBlock) -> None:
        pass
