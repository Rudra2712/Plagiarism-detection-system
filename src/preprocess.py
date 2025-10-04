"""
preprocess.py

Preprocessing utilities:
- Remove comments across common languages (C/C++/Java/JS/Python).
- Normalize whitespace.
- Tokenize into language-agnostic tokens.
- Normalize identifiers and literals to reduce false negatives across renamings.

Design:
- Comment stripping uses regular expressions for line and block comments.
- Tokenization extracts operators, punctuation, identifiers, numbers, and strings.
- Keywords for several languages are preserved; other identifiers -> 'ID'.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import List

# Common language keywords (union of major sets)
KEYWORDS = set("""
auto break case char const continue default do double else enum extern float for goto if inline int long register
restrict return short signed sizeof static struct switch typedef union unsigned void volatile while
class typename template this new delete public private protected friend virtual operator namespace using try catch throw
import from as pass raise def class return yield lambda with nonlocal global assert del elif except finally for while if else
True False None and or not is in async await
var let const function export default undefined null instanceof typeof super extends
#include define pragma include guard
""".split())

# Ignored / collapsed token classes
ID_TOKEN = "ID"
NUM_TOKEN = "NUM"
STR_TOKEN = "STR"

# Regex patterns for comment removal
LINE_COMMENT_CPP_JS = re.compile(r"//.*?$", re.MULTILINE)
BLOCK_COMMENT_CPP_JS = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT_PY = re.compile(r"#[^\n]*", re.MULTILINE)
# Python triple-quoted strings (often used as docstrings). We treat them like comments for normalization.
PY_TRIPLE_STR = re.compile(r"(?:'''(?:.|\n)*?'''|\"\"\"(?:.|\n)*?\"\"\")", re.MULTILINE)

# String and number literals
STRING_LITERAL = re.compile(
    r"""(\"([^\"\\]|\\.)*\"|\'([^\'\\]|\\.)*\')""",
    re.MULTILINE,
)
NUMBER_LITERAL = re.compile(r"\b(?:0x[0-9a-fA-F]+|\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\b")

# Identifiers (broad)
IDENTIFIER = re.compile(r"\b[_A-Za-z]\w*\b")

# Operators and punctuation (kept as tokens)
OPERATORS_PUNCT = re.compile(r"(\+\+|--|==|!=|<=|>=|<<=|>>=|->|&&|\|\||<<|>>|::|\+=|-=|\*=|/=|%=|&=|\^=|\|=|=|[+\-*/%&|\^~!<>?:;,.()\[\]{}])")

WHITESPACE = re.compile(r"\s+")


def strip_comments(text: str, suffix: str) -> str:
    """
    Remove comments for C/C++/Java/JS and Python-like files.
    """
    # Remove block comments /* ... */ and // line comments (C-like)
    text = re.sub(BLOCK_COMMENT_CPP_JS, "", text)
    text = re.sub(LINE_COMMENT_CPP_JS, "", text)

    # Python-specific: remove triple-quoted strings (treated as comments/docstrings) and # line comments
    if suffix in {".py"}:
        text = re.sub(PY_TRIPLE_STR, "", text)
        text = re.sub(LINE_COMMENT_PY, "", text)
    else:
        # Even for non-py, remove # lines commonly used in shell/py
        text = re.sub(LINE_COMMENT_PY, "", text)
    return text


def normalize_whitespace(text: str) -> str:
    """Collapse whitespace to single spaces and strip."""
    return re.sub(WHITESPACE, " ", text).strip()


def tokenize(text: str) -> List[str]:
    """
    Tokenize into a sequence of language-agnostic tokens.
    - Keep operators/punct as-is.
    - Replace strings with STR, numbers with NUM.
    - Preserve known keywords; map other identifiers to ID.
    """
    tokens: List[str] = []
    i = 0
    n = len(text)

    # Pre-replace literals to placeholders to avoid double-tokenization
    def mark_literals(s: str) -> str:
        s = re.sub(STRING_LITERAL, STR_TOKEN, s)
        s = re.sub(NUMBER_LITERAL, NUM_TOKEN, s)
        return s

    text = mark_literals(text)

    # Split by operators/punctuation and words
    parts = re.split(OPERATORS_PUNCT, text)
    # re.split keeps delimiters; re.findall helps to re-collect them
    delims = re.findall(OPERATORS_PUNCT, text)

    # Merge sequence: part0, delim0, part1, delim1, ...
    merged: List[str] = []
    for idx, part in enumerate(parts):
        if part:
            merged.append(part)
        if idx < len(delims):
            merged.append(delims[idx])

    for piece in merged:
        piece = piece.strip()
        if not piece:
            continue
        if piece in {STR_TOKEN, NUM_TOKEN}:
            tokens.append(piece)
            continue
        # Identify identifiers / keywords
        for tok in re.findall(r"[_A-Za-z]\w*|\S", piece):
            if tok.isidentifier():
                low = tok.lower()
                if low in KEYWORDS:
                    tokens.append(low)
                else:
                    tokens.append(ID_TOKEN)
            else:
                tokens.append(tok)
    return tokens


def preprocess_code(text: str, file_path: Path) -> List[str]:
    """
    Full preprocessing for a file:
    - Strip comments
    - Normalize whitespace
    - Tokenize
    Returns a list of tokens.
    """
    suffix = file_path.suffix.lower()
    no_comments = strip_comments(text, suffix)
    normalized = normalize_whitespace(no_comments)
    tokens = tokenize(normalized)
    return tokens


__all__ = ["preprocess_code"]
