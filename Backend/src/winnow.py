"""
winnow.py

Winnowing algorithm to select representative fingerprints from a rolling-hash sequence.

Given a list of (hash, position) for shingles and a window size w:
- Slide a window of size w across the sequence.
- Select the minimum hash in each window. If multiple minima, choose the rightmost.
- Return a set of fingerprints as (hash, position_of_selected_min).

This reduces sensitivity to small edits and yields stable fingerprints.
"""

from __future__ import annotations
from typing import Iterable, List, Set, Tuple

DEFAULT_W = 4

def winnow(hashes: List[Tuple[int, int]], w: int = DEFAULT_W) -> Set[Tuple[int, int]]:
    """
    Apply winnowing to a list of (hash, pos). Returns a set of selected (hash, pos).
    """
    if w <= 0 or not hashes:
        return set()

    selected: Set[Tuple[int, int]] = set()
    n = len(hashes)
    window = []  # holds indices into 'hashes'

    # Initialize first window
    for i in range(min(w, n)):
        window.append(i)

    def pick_min(window_indices: List[int]) -> Tuple[int, int]:
        # Returns (hash, pos) of the rightmost minimum in current window
        min_hash = None
        min_idx = None
        for idx in window_indices:
            h, pos = hashes[idx]
            if (min_hash is None) or (h < min_hash) or (h == min_hash and idx > (min_idx or -1)):
                min_hash = h
                min_idx = idx
        return hashes[min_idx]

    # Pick for first window
    min_pair = pick_min(window)
    selected.add(min_pair)

    # Slide window
    for right in range(w, n):
        window.pop(0)
        window.append(right)
        new_min_pair = pick_min(window)
        if new_min_pair != min_pair:
            selected.add(new_min_pair)
            min_pair = new_min_pair

    return selected
