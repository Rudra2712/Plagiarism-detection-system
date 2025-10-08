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
) -> Dict[str, List[Dict]]:
    """
    Compare each pair of assignments and report suspicious pairs and file-level details.
    Returns dict:
      {
        "suspiciousPairs": [(A, B), ...],
        "details": [
            {
                "pair": (A, B),
                "topAtoB": [(fa, fb, similarityPct), ...],
                "topBtoA": [(fb, fa, similarityPct), ...]
            },
            ...
        ]
      }
    """
    file_hash_sets: Dict[str, Set[int]] = {
        fid: set_of_hashes(fps) for fid, fps in file_fps.items()
    }

    suspicious_pairs = []
    details = []
    names = sorted(assignments.keys())

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            files_a = [str(p) for p in assignments[a] if str(p) in file_hash_sets]
            files_b = [str(p) for p in assignments[b] if str(p) in file_hash_sets]
            if not files_a or not files_b:
                continue

            hash_only_fps = {fid: file_hash_sets[fid] for fid in (files_a + files_b)}

            flag, best_a_to_b, best_b_to_a = is_assignment_pair_suspicious(
                files_a, files_b, hash_only_fps, file_threshold, assignment_threshold
            )

            if flag:
                suspicious_pairs.append((a, b))

            top_a = summarize_pair_details(best_a_to_b, top_k=5)
            top_b = summarize_pair_details(best_b_to_a, top_k=5)

            details.append({
                "pair": (a, b),
                "topAtoB": [
                    {"left": fa, "right": fb, "similarityPct": s * 100}
                    for fa, fb, s in top_a
                ],
                "topBtoA": [
                    {"left": fb, "right": fa, "similarityPct": s * 100}
                    for fb, fa, s in top_b
                ],
            })

    return {"suspiciousPairs": suspicious_pairs, "details": details}



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
    results = compare_assignments(
        assignments,
        file_fps,
        file_threshold=args.file_threshold,
        assignment_threshold=args.assignment_threshold,
        show_details=args.show_details 
    )

    print("\nSuspicious Assignment Pairs:")
    if not results["suspiciousPairs"]:
        print("(none)")
    else:
        for a, b in results["suspiciousPairs"]:
            print(f"{a} <-> {b}")

    if args.show_details:
        # Emit detailed sections in the exact format expected by the backend parser
        for d in results.get("details", []):
            a, b = d.get("pair", ("A", "B"))
            print("")
            print(f"--- Details for pair: {a} <-> {b} ---")
            print("Top matches A -> B")
            for rec in d.get("topAtoB", []):
                left = rec.get("left", "")
                right = rec.get("right", "")
                pct = float(rec.get("similarityPct", 0.0))
                print(f"{left} ~~ {pct:.2f}% ~~ {right}")
            print("")
            print("Top matches B -> A")
            for rec in d.get("topBtoA", []):
                left = rec.get("left", "")
                right = rec.get("right", "")
                pct = float(rec.get("similarityPct", 0.0))
                print(f"{left} ~~ {pct:.2f}% ~~ {right}")



if __name__ == "__main__":
    main()
