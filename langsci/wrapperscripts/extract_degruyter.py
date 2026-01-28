#!/usr/bin/env python3
"""
Extract IGT examples from PDFs using PyMuPDF ONLY, with reconstruction by halving lines.

NEW (per user):
- Subexample labels "a.", "b.", ... are additional *opening signals*.
- Each subexample closes at its own translation line (quoted line).
- Subexamples MUST have a mother numerical example "(23)".
- When reporting a subexample, also output the mother example id.
- Abort reconstruction if ANY list item in either half (post-parity, post-empty-removal)
  is longer than 50 characters.

Still:
- No langdetect.
- No general line joining.
- Print RAW MATCH before any parsing/validation.
- Reconstruction: upper half -> source, lower half -> gloss (space-joined)
- Skip odd-cardinality lists unless oddness disappears after removing empty lines.
- Validate: both source & gloss contain '-' or '=' AND have equal token counts.

Output (for successful parses):
mother: ...
number: ...        (mother or mother+sub)
language: ...      (if detected)
igt: ...
translation: ...
based on: [full match]

For RAW MATCH (always printed for each finalized block):
RAW MATCH:
[ ... ]
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ----------------------------
# Normalization
# ----------------------------

MULTISPACE = re.compile(r"[ \t]+")
PUNCT_EDGE = re.compile(r"^[^\w]+|[^\w]+$")


def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = s.replace("\r", " ").replace("\n", " ")
    return MULTISPACE.sub(" ", s).strip()


def normalize_line(s: str) -> str:
    s = s.replace("\u00ad", "")  # soft hyphen
    s = s.replace("\ufb01", "fi").replace("\ufb02", "fl")
    s = s.replace("\t", " ")
    return normalize_text(s)


def word_tokens(s: str) -> List[str]:
    toks: List[str] = []
    for t in normalize_text(s).split():
        t2 = PUNCT_EDGE.sub("", t)
        if t2:
            toks.append(t2)
    return toks


# ----------------------------
# PDF extraction (PyMuPDF only)
# ----------------------------

def extract_pdf_lines(pdf_path: str) -> List[str]:
    try:
        import pymupdf as fitz  # PyMuPDF ≥ 1.23
    except ImportError:
        import fitz  # type: ignore

    lines: List[str] = []
    doc = fitz.open(pdf_path)

    for page in doc:
        page_dict = page.get_text("dict")
        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                txt = "".join(sp.get("text", "") for sp in spans if sp.get("text"))
                txt = normalize_line(txt)
                if txt:
                    lines.append(txt)
        lines.append("")  # page break marker

    doc.close()
    return lines


# ----------------------------
# Signals & detection
# ----------------------------

RE_EX_START = re.compile(r"^\((\d+)\)\s*(.*)$")
RE_SUBLABEL = re.compile(r"^([a-z])\.\s*(.*)$", re.IGNORECASE)

# Translation line: contains a quoted span (backtick allowed).
RE_QUOTED_SPAN = re.compile(r"[\"“‘`].+?[\"”’']")


def has_translation_signal(line: str) -> bool:
    return bool(RE_QUOTED_SPAN.search(line))


def extract_translation(line: str) -> str:
    m = RE_QUOTED_SPAN.search(line)
    if not m:
        return ""
    t = m.group(0)
    return normalize_text(t.strip("“”\"").strip("‘’'").strip("`"))


def has_morph_seps(s: str) -> bool:
    return "-" in s or "=" in s


# Optional language line detection (kept; no langdetect)
RE_LANG_HEADER = re.compile(r"^([A-Z][^()]+?)\s*\((.+?)\)\s*$")


def is_language_line(line: str) -> bool:
    line = normalize_line(line)
    if not line:
        return False
    if has_translation_signal(line):
        return False
    if RE_EX_START.match(line):
        return False
    if RE_SUBLABEL.match(line):
        return False
    if has_morph_seps(line):
        return False
    if RE_LANG_HEADER.match(line):
        return True
    words = line.split()
    if 1 <= len(words) <= 8 and line[:1].isupper() and not line.endswith((".", "!", "?", "…")):
        return True
    return False


# ----------------------------
# Reconstruction logic
# ----------------------------

MAX_ITEM_LEN = 50


def reconstruct_igt(between_lines: List[str]) -> Optional[Tuple[str, str]]:
    """
    Reconstruct (source, gloss) from content lines between opening and closing.

    Parity rule:
    - If count is even -> OK.
    - If odd -> remove empty lines and re-check; proceed if even.
    - Otherwise reject.

    Additional rule:
    - After choosing the working list, split into halves.
    - If ANY element in either half is > 50 characters, abort reconstruction.
    """
    raw = [normalize_line(x) for x in between_lines]
    nonempty = [x for x in raw if x.strip()]

    if len(raw) % 2 != 0:
        if len(nonempty) % 2 != 0:
            return None
        work = nonempty
    else:
        work = raw
        if any(not x.strip() for x in work):
            work = nonempty
            if len(work) % 2 != 0:
                return None

    if not work or len(work) < 2 or len(work) % 2 != 0:
        return None

    half = len(work) // 2
    upper = work[:half]
    lower = work[half:]

    # abort if any item too long
    if any(len(x) > MAX_ITEM_LEN for x in upper):
        return None
    if any(len(x) > MAX_ITEM_LEN for x in lower):
        return None

    source = normalize_text(" ".join(upper))
    gloss = normalize_text(" ".join(lower))

    if not source or not gloss:
        return None

    return source, gloss


# ----------------------------
# Streaming state
# ----------------------------

@dataclass
class Block:
    """
    A block is either:
    - mother example block (sub_id = "")
    - subexample block (sub_id = "a", "b", ...)
    It starts at an opening signal and ends at its own translation line.
    """
    mother_id: str
    sub_id: str  # "" for mother block, else "a"/"b"/...
    open_line: str
    lang_line: str = ""
    between: List[str] = field(default_factory=list)  # content lines for reconstruction
    raw_between: List[str] = field(default_factory=list)  # for RAW MATCH (includes language lines etc. as encountered)


def block_number(b: Block) -> str:
    return f"{b.mother_id}{b.sub_id}" if b.sub_id else b.mother_id


def print_raw_match(b: Block, closing_line: str) -> List[str]:
    """
    Print RAW MATCH and return the full block lines (normalized) used for 'based on'.
    RAW MATCH is from the opening signal line through the closing translation line, inclusive.
    """
    open_line = normalize_line(b.open_line)
    closing = normalize_line(closing_line)

    raw_block: List[str] = [open_line]
    if b.lang_line:
        raw_block.append(normalize_line(b.lang_line))
    for ln in b.raw_between:
        raw_block.append(normalize_line(ln))
    raw_block.append(closing)

    print("RAW MATCH:")
    print("[")
    for ln in raw_block:
        print(ln)
    print("]")
    print()

    return [ln for ln in raw_block if ln]


def finalize_block(b: Block, closing_line: str) -> None:
    """
    Always prints RAW MATCH. Then attempts reconstruction + checks; if pass, prints structured output.
    """
    full_lines = print_raw_match(b, closing_line)

    translation = extract_translation(closing_line)
    if not translation:
        return

    recon = reconstruct_igt(b.between)
    if not recon:
        return

    source_line, gloss_line = recon

    # Checks requested earlier
    if not has_morph_seps(source_line):
        return
    if not has_morph_seps(gloss_line):
        return
    if len(word_tokens(source_line)) != len(word_tokens(gloss_line)):
        return

    based_on = normalize_text(" ".join(full_lines))

    print(f"mother: {b.mother_id}")
    print(f"number: {block_number(b)}")
    print(f"language: {normalize_line(b.lang_line)}")
    print(f"igt: {source_line} || {gloss_line}")
    print(f"translation: {translation}")
    print(f"based on: [{based_on}]")
    print()


# ----------------------------
# Parser
# ----------------------------

def parse_and_stream(lines: List[str], min_n: int, max_n: int) -> None:
    mother_id: Optional[str] = None
    mother_open_line: str = ""
    mother_lang_line: str = ""

    current: Optional[Block] = None
    have_seen_subs = False

    def close_current_if_translation(line: str) -> bool:
        nonlocal current
        if current is not None and line and has_translation_signal(line):
            finalize_block(current, line)
            current = None
            return True
        return False

    for raw in lines:
        line = normalize_line(raw)

        # Start of a new mother example?
        m_ex = RE_EX_START.match(line)
        if m_ex:
            # Starting a new mother implicitly ends any open block WITHOUT printing (no closing signal).
            current = None
            have_seen_subs = False

            ex_id = m_ex.group(1)
            try:
                n = int(ex_id)
            except ValueError:
                mother_id = None
                continue

            if not (min_n <= n <= max_n):
                mother_id = None
                continue

            mother_id = ex_id
            mother_open_line = line
            mother_lang_line = ""

            # Create a mother block immediately (so mother can close on its own translation)
            current = Block(
                mother_id=mother_id,
                sub_id="",
                open_line=mother_open_line,
                lang_line="",
                between=[],
                raw_between=[]
            )

            rest = normalize_text(m_ex.group(2))
            if rest:
                # This "rest" can be language line or content. Store in raw_between always.
                current.raw_between.append(rest)
                # If it looks like language, keep it; else treat as content.
                if current.lang_line == "" and is_language_line(rest):
                    current.lang_line = rest
                    mother_lang_line = rest
                else:
                    current.between.append(rest)
            continue

        # If there's no mother, subexamples must not start
        if mother_id is None:
            continue

        # If current block closes here, do it and keep scanning.
        if close_current_if_translation(line):
            continue

        # Subexample opening signal?
        m_sub = RE_SUBLABEL.match(line)
        if m_sub:
            # Subexamples must have a mother id (guaranteed by mother_id check above)
            have_seen_subs = True

            sub_id = m_sub.group(1).lower()
            rest = normalize_text(m_sub.group(2))

            # Start a new sub-block; it will close on its own translation line.
            # Note: mother_lang_line may have been captured earlier. Sub can also have its own language line.
            current = Block(
                mother_id=mother_id,
                sub_id=sub_id,
                open_line=f"{sub_id}.",
                lang_line="",
                between=[],
                raw_between=[]
            )

            # If "a. ..." has trailing text, it could be language or content.
            if rest:
                current.raw_between.append(rest)
                if current.lang_line == "" and is_language_line(rest):
                    current.lang_line = rest
                else:
                    current.between.append(rest)
            continue

        # Otherwise: line inside whatever block is current, or part of mother context.
        if current is None:
            # Not currently inside a block; we ignore until we hit a sublabel or a new mother.
            # (Subexamples should start with "a." etc.)
            continue

        # Allow language line either:
        # - between mother number and first sublabel (goes to mother block)
        # - between sublabel and first source word (goes to that sub block)
        if current.lang_line == "" and is_language_line(line):
            current.lang_line = line
            if current.sub_id == "":
                mother_lang_line = line
            else:
                # If mother language not set, inherit for reporting purposes only
                pass
            # still keep for RAW MATCH
            current.raw_between.append(line)
            continue

        # Content line
        if raw.strip() == "":
            # keep empties in raw_between to preserve parity logic; also keep in between
            current.raw_between.append("")
            current.between.append("")
        else:
            current.raw_between.append(line)
            current.between.append(line)

    # EOF: no implicit close; blocks require an explicit closing translation line.


# ----------------------------
# Main
# ----------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", help="Input PDF path")
    ap.add_argument("--min", type=int, default=1)
    ap.add_argument("--max", type=int, default=10_000)
    args = ap.parse_args()

    if not os.path.exists(args.pdf):
        print(f"ERROR: PDF not found: {args.pdf}", file=sys.stderr)
        return 2

    lines = extract_pdf_lines(args.pdf)
    parse_and_stream(lines, args.min, args.max)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
