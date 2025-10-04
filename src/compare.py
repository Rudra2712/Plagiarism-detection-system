"""
compare.py

Performs comparisons at file and assignment levels using:
- Jaccard similarity on fingerprint sets for files.
- Aggregation rule at assignment level:
  If ≥ assignment_threshold of files in either assignment have a file-level similarity
  ≥ file_threshold with some file in the other assignment, mark the pair as suspicious.

Also provides helpers to compute shared fingerprint counts and pick best matches.
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Set
from collections import defaultdict


def jaccard_similarity(fps_a: Set[int], fps_b: Set[int]) -> float:
    if not fps_a and not fps_b:
        return 0.0
    inter = len(fps_a & fps_b)
    union = len(fps_a | fps_b)
    return inter / union if union else 0.0


def file_similarity_matrix(
    file_ids_a: List[str],
    file_ids_b: List[str],
    file_fps: Dict[str, Set[int]],
) -> Dict[Tuple[str, str], float]:
    """
    Compute pairwise file similarities (Jaccard) between two sets of files.
    Returns dict keyed by (fileA, fileB) -> similarity.
    """
    sim: Dict[Tuple[str, str], float] = {}
    for fa in file_ids_a:
        fps_a = file_fps.get(fa, set())
        for fb in file_ids_b:
            fps_b = file_fps.get(fb, set())
            sim[(fa, fb)] = jaccard_similarity(fps_a, fps_b)
    return sim


def best_match_per_file(
    file_ids_src: List[str],
    file_ids_dst: List[str],
    file_fps: Dict[str, Set[int]]
) -> Dict[str, Tuple[str, float]]:
    """
    For each file in src, find the single best-matching file in dst.
    Returns mapping: src_file -> (best_dst_file, similarity)
    """
    best: Dict[str, Tuple[str, float]] = {}
    for fa in file_ids_src:
        best_score = -1.0
        best_fb = None
        fps_a = file_fps.get(fa, set())
        for fb in file_ids_dst:
            fps_b = file_fps.get(fb, set())
            score = jaccard_similarity(fps_a, fps_b)
            if score > best_score:
                best_score = score
                best_fb = fb
        best[fa] = (best_fb, best_score if best_fb is not None else 0.0)
    return best


def is_assignment_pair_suspicious(
    files_a: List[str],
    files_b: List[str],
    file_fps: Dict[str, Set[int]],
    file_threshold: float,
    assignment_threshold: float
) -> Tuple[bool, Dict[str, Tuple[str, float]], Dict[str, Tuple[str, float]]]:
    """
    Decide if assignments are suspicious based on thresholds.
    Returns:
      (flag, best_map_AtoB, best_map_BtoA)
    """
    best_a_to_b = best_match_per_file(files_a, files_b, file_fps)
    best_b_to_a = best_match_per_file(files_b, files_a, file_fps)

    def fraction_meeting_threshold(best_map: Dict[str, Tuple[str, float]]) -> float:
        if not best_map:
            return 0.0
        count = sum(1 for _, (_, s) in best_map.items() if s >= file_threshold)
        return count / max(1, len(best_map))

    frac_a = fraction_meeting_threshold(best_a_to_b)
    frac_b = fraction_meeting_threshold(best_b_to_a)

    suspicious = (frac_a >= assignment_threshold) or (frac_b >= assignment_threshold)
    return suspicious, best_a_to_b, best_b_to_a


def summarize_pair_details(
    best_map: Dict[str, Tuple[str, float]],
    top_k: int = 5
) -> List[Tuple[str, str, float]]:
    """
    Returns top_k matches sorted by similarity: (src_file, dst_file, similarity).
    """
    items = sorted(
        [(fa, fb, s) for fa, (fb, s) in best_map.items()],
        key=lambda x: x[2],
        reverse=True
    )
    return items[:top_k]
