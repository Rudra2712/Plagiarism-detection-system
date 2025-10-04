"""
main.py

Runs the full plagiarism detection pipeline:

1) Walk 'corpus' directory to identify assignments (subfolders).
2) For each file (excluding ignored directories), preprocess -> tokens.
3) Shingling -> rolling Rabin–Karp hashes.
4) Winnowing -> fingerprints for each file.
5) Build inverted index (not strictly required for Jaccard; useful for extension/bonus).
6) Compare all assignment pairs:
   - File-level Jaccard similarity on fingerprint sets.
   - Assignment-level aggregation: if ≥ assignment_threshold of files in either
     assignment have ≥ file_threshold match with some file in the other assignment,
     mark as suspicious.

Console-friendly output is printed.

Bonus: With --show-details, prints top file matches with similarity scores.
"""

from __future__ import annotations
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

from .preprocess import preprocess_code
from .shingle import rolling_hashes, DEFAULT_K
from .winnow import winnow, DEFAULT_W
from .indexer import InvertedIndex
from .compare import is_assignment_pair_suspicious, summarize_pair_details


DEFAULT_FILE_THRESHOLD = 0.40
DEFAULT_ASSIGNMENT_THRESHOLD = 0.40

DEFAULT_IGNORES = {
    "node_modules", ".git", ".hg", ".svn", ".idea", ".vs", ".vscode",
    ".venv", "venv", "__pycache__", "dist", "build", "target", "out"
}

TEXT_FILE_SUFFIXES = {
    ".c", ".h", ".cpp", ".hpp", ".cc", ".hh", ".cxx", ".hxx",
    ".java", ".js", ".jsx", ".ts", ".tsx",
    ".py", ".rb", ".go", ".rs", ".swift", ".kt", ".kts",
    ".cs", ".m", ".mm",
    ".php", ".html", ".css", ".scss", ".sql", ".sh", ".bat", ".ps1",
    ".r", ".jl", ".pl", ".lua"
}


def collect_assignments(corpus_dir: Path, ignores: Set[str]) -> Dict[str, List[Path]]:
    """
    Returns: mapping assignment_name -> list of file paths to include.
    Each immediate subdirectory of `corpus_dir` is treated as one assignment.
    """
    assignments: Dict[str, List[Path]] = {}
    if not corpus_dir.exists():
        raise FileNotFoundError(f"Corpus directory not found: {corpus_dir}")

    for sub in sorted(p for p in corpus_dir.iterdir() if p.is_dir()):
        files: List[Path] = []
        for path in sub.rglob("*"):
            if path.is_dir():
                # Skip ignored directory names
                if path.name in ignores:
                    # Skip walking deeper by not adding; rglob will still descend, but we filter files
                    continue
                continue
            if path.name.startswith("."):  # hidden files
                continue
            if any(part in ignores for part in path.parts):
                continue
            if path.suffix.lower() in TEXT_FILE_SUFFIXES:
                files.append(path)
        assignments[sub.name] = sorted(files)
    return assignments


def compute_file_fingerprints(
    files: List[Path],
    k: int,
    w: int
) -> Dict[str, Set[Tuple[int, int]]]:
    """
    For each file path, compute fingerprints via shingling + rolling hash + winnowing.
    Returns mapping file_id (str) -> set of (hash, position)
    """
    file_fps: Dict[str, Set[Tuple[int, int]]] = {}
    for fpath in files:
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            # Fallback to binary read and decode as latin-1; last resort
            text = fpath.read_bytes().decode("latin-1", errors="ignore")

        tokens = preprocess_code(text, fpath)
        rh = rolling_hashes(tokens, k=k)
        fps = winnow(rh, w=w)
        file_fps[str(fpath)] = set((h, pos) for (h, pos) in fps)
    return file_fps


def set_of_hashes(fps: Set[Tuple[int, int]]) -> Set[int]:
    """Drop positions; keep only hash values for Jaccard."""
    return {h for (h, _) in fps}


def build_index(file_fps: Dict[str, Set[Tuple[int, int]]]) -> InvertedIndex:
    """
    Build an inverted index of fingerprints. Could be used for bonus highlighting.
    """
    idx = InvertedIndex()
    for fid, fps in file_fps.items():
        idx.add(fid, fps)
    return idx


def compare_assignments(
    assignments: Dict[str, List[Path]],
    file_fps: Dict[str, Set[Tuple[int, int]]],
    file_threshold: float,
    assignment_threshold: float,
    show_details: bool = False
) -> List[Tuple[str, str]]:
    """
    Compare each pair of assignments and report suspicious pairs.
    Returns list of suspicious (A, B) pairs.
    """
    # Precompute file hash-sets for faster Jaccard
    file_hash_sets: Dict[str, Set[int]] = {
        fid: set_of_hashes(fps) for fid, fps in file_fps.items()
    }

    suspicious_pairs: List[Tuple[str, str]] = []
    names = sorted(assignments.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            files_a = [str(p) for p in assignments[a]]
            files_b = [str(p) for p in assignments[b]]

            # Filter to those actually processed (in case some files are unsupported)
            files_a = [f for f in files_a if f in file_hash_sets]
            files_b = [f for f in files_b if f in file_hash_sets]

            if not files_a or not files_b:
                continue

            # Use compare.is_assignment_pair_suspicious with prepared sets
            # Wrap file_fps to deliver only hash sets
            hash_only_fps = {fid: file_hash_sets[fid] for fid in (files_a + files_b)}
            flag, best_a_to_b, best_b_to_a = is_assignment_pair_suspicious(
                files_a, files_b, hash_only_fps, file_threshold, assignment_threshold
            )

            if flag:
                suspicious_pairs.append((a, b))

            if show_details:
                print("\n--- Details for pair:", a, "<->", b, "---")
                top_a = summarize_pair_details(best_a_to_b, top_k=5)
                top_b = summarize_pair_details(best_b_to_a, top_k=5)

                def short(p: str) -> str:
                    return "/".join(Path(p).parts[-2:])

                print("Top matches A→B:")
                for fa, fb, s in top_a:
                    print(f"  {short(fa)}  ~~ {s:.2%} ~~  {short(fb)}")
                print("Top matches B→A:")
                for fb, fa, s in top_b:
                    print(f"  {short(fb)}  ~~ {s:.2%} ~~  {short(fa)}")

    return suspicious_pairs


def main():
    parser = argparse.ArgumentParser(description="Plagiarism Checker for Code Assignments")
    parser.add_argument("--corpus", type=str, default="corpus", help="Root folder of assignments")
    parser.add_argument("--k", type=int, default=DEFAULT_K, help="Shingle size")
    parser.add_argument("--w", type=int, default=DEFAULT_W, help="Winnowing window size")
    parser.add_argument("--file-threshold", type=float, default=DEFAULT_FILE_THRESHOLD, help="File-level Jaccard similarity threshold")
    parser.add_argument("--assignment-threshold", type=float, default=DEFAULT_ASSIGNMENT_THRESHOLD, help="Assignment-level fraction threshold")
    parser.add_argument("--ignore", type=str, default="", help="Comma-separated list of additional folders to ignore")
    parser.add_argument("--show-details", action="store_true", help="Show top file match details")

    args = parser.parse_args()

    corpus_dir = Path(args.corpus)
    ignores = set(DEFAULT_IGNORES)
    if args.ignore:
        ignores |= {x.strip() for x in args.ignore.split(",") if x.strip()}

    assignments = collect_assignments(corpus_dir, ignores)

    # Flatten all files for footprinting
    all_files = [p for files in assignments.values() for p in files]
    file_fps = compute_file_fingerprints(all_files, k=args.k, w=args.w)

    # Optional: build index (currently not required for core flow; kept for extension/bonus)
    _ = build_index(file_fps)

    # Compare
    suspicious = compare_assignments(
        assignments,
        file_fps,
        file_threshold=args.file_threshold,
        assignment_threshold=args.assignment_threshold,
        show_details=args.show_details
    )

    print("\nSuspicious Assignment Pairs:")
    if not suspicious:
        print("(none)")
    else:
        for a, b in suspicious:
            print(f"{a} ↔ {b}")


if __name__ == "__main__":
    main()
