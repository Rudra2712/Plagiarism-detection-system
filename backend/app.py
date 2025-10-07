from __future__ import annotations
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

# 🔧 Base setup
BASE_DIR = Path(__file__).resolve().parents[1]
CORPUS_DIR = (BASE_DIR / "corpus").resolve()
ALLOWED_EXTENSIONS = {".cpp"}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB per request
PER_FILE_MAX = 10 * 1024 * 1024  # 10 MB per file
SUBPROCESS_TIMEOUT = 120  # seconds for plagiarism check subprocess

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("plagiarism_service")

def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.get("/api/health")
    def health() -> Any:
        return jsonify({"status": "ok"})

    # -----------------------------------------
    # ✅ FILE UPLOAD HANDLER (kept as-is)
    # -----------------------------------------
    @app.post("/api/upload")
    def upload() -> Any:
        if "files" not in request.files:
            return jsonify({"error": "No files part in request"}), 400

        files = request.files.getlist("files")
        if not files:
            return jsonify({"error": "No files uploaded"}), 400

        assignment_name = request.form.get("assignment", "Upload")
        assignment_name = re.sub(r"[^A-Za-z0-9._-]", "_", assignment_name).strip("._-") or "Upload"

        target_dir = (CORPUS_DIR / assignment_name).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        try:
            target_dir.relative_to(CORPUS_DIR)
        except Exception:
            return jsonify({"error": "Invalid assignment path"}), 400

        saved: List[str] = []
        for f in files:
            filename = secure_filename(f.filename or "")
            if not filename:
                return jsonify({"error": "One of the files has no name"}), 400

            suffix = Path(filename).suffix.lower()
            if suffix not in ALLOWED_EXTENSIONS:
                return jsonify({"error": f"Invalid extension for {filename}. Only .cpp allowed."}), 400

            dest = (target_dir / filename).resolve()
            try:
                dest.relative_to(CORPUS_DIR)
            except Exception:
                return jsonify({"error": "Invalid filename/path detected"}), 400

            total = 0
            try:
                with open(dest, "wb") as out:
                    try:
                        f.stream.seek(0)
                    except Exception:
                        pass
                    while True:
                        chunk = f.stream.read(8192)
                        if not chunk:
                            break
                        out.write(chunk)
                        total += len(chunk)
                        if total > PER_FILE_MAX:
                            out.close()
                            dest.unlink(missing_ok=True)
                            return jsonify({"error": f"File {filename} exceeds per-file size limit"}), 413
            except Exception as e:
                logger.exception("Failed to save uploaded file: %s", e)
                return jsonify({"error": "Failed to save uploaded file"}), 500

            saved.append(str(dest.relative_to(BASE_DIR)))

        return jsonify({"message": "Uploaded", "assignment": assignment_name, "files": saved})

    # -----------------------------------------
    # ✅ RUN PLAGIARISM CHECK (MAIN CHANGE HERE)
    # -----------------------------------------
    @app.post("/api/check")
    def run_check() -> Any:
        # Log directory contents for debugging
        logger.info("Checking corpus directory: %s", CORPUS_DIR)
        assignment_dirs = [d for d in CORPUS_DIR.iterdir() if d.is_dir()]
        for d in assignment_dirs:
            files = list(d.glob("*.cpp"))
            logger.info("Assignment %s contains %d .cpp files: %s", 
                       d.name, len(files), [f.name for f in files])

        cmd = [sys.executable, "-m", "src.main", "--corpus", str(CORPUS_DIR), "--show-details"]
        logger.info("Running check with command: %s", " ".join(cmd))
        logger.info("Working directory: %s", BASE_DIR)

        try:
            # Set explicit encoding and error handler for subprocess
            proc = subprocess.run(
                cmd,
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace invalid chars instead of failing
                check=False,
                timeout=SUBPROCESS_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            return jsonify({"error": "Plagiarism check timed out"}), 504
        except Exception as e:
            logger.exception("Failed to run plagiarism check: %s", e)
            return jsonify({"error": f"Failed to run plagiarism check: {e}"}), 500

        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        if proc.returncode != 0:
            logger.error("Plagiarism check failed with code %d", proc.returncode)
            logger.error("STDERR: %s", stderr)
            logger.error("STDOUT: %s", stdout)
            return jsonify({
                "error": "Plagiarism check failed", 
                "stderr": stderr, 
                "stdout": stdout,
                "returncode": proc.returncode
            }), 500

        parsed = parse_main_output(stdout)

        # 🔥 NEW SECTION — Identify Most Plagiarized Pair
        top_pair = None
        max_similarity = 0.0
        for d in parsed.get("details", []):
            for rec in d.get("topAtoB", []):
                if rec["similarityPct"] > max_similarity:
                    max_similarity = rec["similarityPct"]
                    top_pair = (rec["left"], rec["right"])
            for rec in d.get("topBtoA", []):
                if rec["similarityPct"] > max_similarity:
                    max_similarity = rec["similarityPct"]
                    top_pair = (rec["left"], rec["right"])

        parsed["mostPlagiarized"] = {
            "pair": top_pair,
            "similarity": round(max_similarity, 2),
        } if top_pair else None

        return jsonify({"stdout": stdout, "results": parsed})

    # -----------------------------------------
    # ✅ CLEANUP ENDPOINT (as-is)
    # -----------------------------------------
    @app.post("/api/cleanup")
    def cleanup() -> Any:
        removed: List[str] = []
        for path in CORPUS_DIR.rglob("*.cpp"):
            try:
                p_resolved = path.resolve()
                p_resolved.relative_to(CORPUS_DIR)
                p_resolved.unlink()
                removed.append(str(p_resolved.relative_to(BASE_DIR)))
            except Exception:
                continue

        for sub in sorted((p for p in CORPUS_DIR.iterdir() if p.is_dir()), key=lambda p: -len(str(p))):
            try:
                if not any(sub.iterdir()):
                    sub.rmdir()
            except Exception:
                pass

        return jsonify({"message": "Cleanup complete", "removed": removed})

    return app

# -----------------------------------------
# ✅ PARSER UTILITIES (unchanged)
# -----------------------------------------
def parse_main_output(text: str) -> Dict[str, Any]:
    lines = [ln.rstrip() for ln in text.splitlines()]
    details: List[Dict[str, Any]] = []
    suspicious_pairs: List[List[str]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^---\s*Details\s*for\s*pair:\s*(.+?)\s*(?:<->|↔)\s*(.+?)\s*---\s*$", line)
        if m:
            a_name, b_name = m.group(1).strip(), m.group(2).strip()
            i += 1
            a_to_b, b_to_a = [], []
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            if i < len(lines) and re.match(r"^\s*Top\s+matches\s*A", lines[i], re.I):
                i += 1
                while i < len(lines):
                    if lines[i].strip() == "":
                        i += 1
                        continue
                    if re.match(r"^\s*Top\s+matches\s*B", lines[i], re.I) or re.match(r"^---", lines[i]):
                        break
                    rec = parse_match_line(lines[i])
                    if rec:
                        a_to_b.append(rec)
                    i += 1
            if i < len(lines) and re.match(r"^\s*Top\s+matches\s*B", lines[i], re.I):
                i += 1
                while i < len(lines):
                    if lines[i].strip() == "":
                        i += 1
                        continue
                    if re.match(r"^---", lines[i]):
                        break
                    rec = parse_match_line(lines[i])
                    if rec:
                        b_to_a.append(rec)
                    i += 1
            details.append({"pair": [a_name, b_name], "topAtoB": a_to_b, "topBtoA": b_to_a})
            continue
        i += 1

    for idx, ln in enumerate(lines):
        if ln.strip().startswith("Suspicious Assignment Pairs"):
            j = idx + 1
            while j < len(lines):
                s = lines[j].strip()
                if not s:
                    j += 1
                    continue
                if s == "(none)":
                    break
                m = re.match(r"^(.+?)\s*(?:↔|<->)\s*(.+)$", s)
                if m:
                    suspicious_pairs.append([m.group(1).strip(), m.group(2).strip()])
                j += 1
            break
    return {"details": details, "suspiciousPairs": suspicious_pairs}

def parse_match_line(line: str) -> Dict[str, Any] | None:
    m = re.match(r"^\s*(\S.*\S|\S)\s*~~\s*([0-9]+(?:\.[0-9]+)?)%\s*~~\s*(\S.*\S|\S)\s*$", line)
    if not m:
        return None
    return {"left": m.group(1).strip(), "right": m.group(3).strip(), "similarityPct": float(m.group(2))}

# -----------------------------------------
# ✅ ENTRY POINT
# -----------------------------------------
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True)
