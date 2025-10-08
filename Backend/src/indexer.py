"""
indexer.py

Builds an inverted index from fingerprints:
    fingerprint_hash -> list of (file_id, position)

This allows quick lookup of which files share the same fingerprints.
"""

from __future__ import annotations
from collections import defaultdict
from typing import Dict, List, Tuple, Set


class InvertedIndex:
    def __init__(self) -> None:
        self.map: Dict[int, List[Tuple[str, int]]] = defaultdict(list)

    def add(self, file_id: str, fingerprints: Set[Tuple[int, int]]) -> None:
        """
        Add fingerprints for a file into the index.
        fingerprints: set of (hash, position)
        """
        for h, pos in fingerprints:
            self.map[h].append((file_id, pos))

    def lookup(self, h: int) -> List[Tuple[str, int]]:
        """
        Return list of (file_id, position) where fingerprint h was found.
        """
        return self.map.get(h, [])

    def __len__(self) -> int:
        return len(self.map)
