# Plagiarism Checker for Code Assignments

This tool detects plagiarism across student coding assignments by comparing files pairwise, extracting language-agnostic fingerprints using shingling, Rabin–Karp rolling hashes, and the Winnowing algorithm. It then aggregates file-level similarities to the assignment level.

## How It Works (Pipeline)

1. **Preprocessing**
   - Removes comments (`//`, `/* ... */`, `#`, Python docstrings) and normalizes whitespace.
   - Tokenizes into meaningful tokens (identifiers, keywords, operators, numbers, strings).
   - Normalizes identifiers and literals to reduce the effect of renaming:
     - Identifiers → `ID`
     - Numbers → `NUM`
     - Strings → `STR`
     - Common language keywords are preserved (C/C++/Java/JS/Python sets included).

2. **Shingling**
   - Creates overlapping k-token shingles (default `k=5`).

3. **Rabin–Karp Rolling Hash**
   - Converts shingles to numbers using a polynomial rolling hash:
     ```
     H = (t0*B^(k-1) + t1*B^(k-2) + ... + tk-1) mod P
     ```
     with efficient updates when sliding to the next shingle.

4. **Winnowing**
   - Slides a window of size `w` (default `w=4`) across the hash sequence.
   - Chooses the minimum hash in the window (rightmost on ties) as a **fingerprint**.
   - This ignores small edits and whitespace changes while preserving matches on larger shared regions.

5. **Inverted Index**
   - Builds a mapping `fingerprint → list of (file_id, position)` to accelerate comparisons.

6. **Comparison**
   - **File-level**: Jaccard similarity on fingerprint sets:
     ```
     J(A, B) = |F(A) ∩ F(B)| / |F(A) ∪ F(B)|
     ```
     A file is considered similar if `J ≥ file_threshold` (default `0.40`).
   - **Assignment-level**: If **≥ 40%** of files in **either** assignment each has a match in the other assignment with `J ≥ file_threshold`, mark the pair as suspicious.

7. **Output**
   - Console summary of suspicious assignment pairs.
   - Optional details showing strongest file matches and shared fingerprint counts.

## Skipping Common Libraries

The scanner ignores these directories (configurable):
- `node_modules`, `.git`, `.hg`, `.svn`, `.idea`, `.vs`, `.vscode`, `.venv`, `venv`, `__pycache__`, `dist`, `build`, `target`, `out`.

## Usage

```bash
python -m src.main \
  --corpus ./corpus \
  --k 5 \
  --w 4 \
  --file-threshold 0.40 \
  --assignment-threshold 0.40 \
  --show-details
-

# 1. Navigate to your project folder
cd "E:\vs code\VS CODE\DAA assignment"

# 2. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the plagiarism checker
python -m src.main --corpus ".\corpus" --show-details
