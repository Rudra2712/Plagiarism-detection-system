"""
shingle.py

Creates token shingles and computes Rabin–Karp rolling hashes.

Rabin–Karp rolling hash:
- Represent each token as an integer via a stable mapping (hashing to a bounded space).
- Polynomial rolling hash: H = sum(tok_i * B^(k-i-1)) mod P
- Efficiently update when sliding by removing leading token and adding trailing token.

This yields a sequence of hashes, one per k-token shingle.
"""

from __future__ import annotations
from typing import Iterable, List, Tuple

DEFAULT_K = 5
BASE = 257            # base for polynomial hash
MOD = 2_147_483_647   # large prime (2^31 - 1)

def token_to_int(tok: str) -> int:
    """
    Map token to a stable small integer for the rolling hash.
    We mod by MOD to keep values bounded.
    """
    # Python built-in hash is salted per run; avoid it. Use deterministic.
    val = 0
    for ch in tok:
        val = (val * 131 + ord(ch)) % MOD
    return val


def rolling_hashes(tokens: List[str], k: int = DEFAULT_K) -> List[Tuple[int, int]]:
    """
    Compute rolling Rabin–Karp hashes for k-length shingles.

    Returns: list of (hash_value, start_index)
    """
    n = len(tokens)
    if k <= 0 or n < k:
        return []

    tvals = [token_to_int(t) for t in tokens]

    # Precompute BASE^(k-1) % MOD
    pow_base = 1
    for _ in range(k - 1):
        pow_base = (pow_base * BASE) % MOD

    # Initial hash
    h = 0
    for i in range(k):
        h = (h * BASE + tvals[i]) % MOD
    hashes = [(h, 0)]

    for i in range(1, n - k + 1):
        # Remove oldest: tvals[i-1] * BASE^(k-1)
        leading = (tvals[i - 1] * pow_base) % MOD
        h = (h - leading) % MOD
        # Multiply by base and add new
        h = (h * BASE + tvals[i + k - 1]) % MOD
        hashes.append((h, i))
    return hashes
