#!/usr/bin/env python3
"""
Extract IGT examples from PDFs using PyMuPDF ONLY, with reconstruction by halving lines.

Update (per user):
- If language detection causes reconstruction to fail, we DROP it:
    If reconstruction fails AND the block has a lang_line, we retry once by
    DEMOTING lang_line into the IGT-content stream (prepend it to between-lines),
    and clearing lang_line (so language falls back to inherited_lang_line for subexamples,
    or becomes empty for mother examples).

This specifically addresses cases where a first source-word (esp. in subexamples) was
misclassified as a language line, making the number of IGT lines odd or otherwise broken.

Other behavior retained:
- example_id / subexample_id output keys
- translation may close on same line or next two lines (1–3 lines)
- subexamples inherit language from mother if not specified locally
- reconstruction by halving between-lines
- inside _reconstruct_core: if first attempt fails, drop exactly ONE cell (first of first
  adjacent identical pair) and retry once
- token mismatch repair: collapse adjacent identical tokens and retry once
- morph-separator requirement toggle (--require-morph-seps, default off)
- debug prints raw_match only for failures (never for successes)
- end report: extracted vs raw_matches
- parser-side one-shot de-duplication after opener "rest" to prevent systematic duplicates
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
    s = s.replace("\u00ad", "")
    s = s.replace("\ufb01", "fi").replace("\ufb02", "fl")
    s = s.replace("\t", " ")
    return normalize_text(s)


def tokenized_words(s: str) -> List[str]:
    toks: List[str] = []
    for t in normalize_text(s).split():
        t2 = PUNCT_EDGE.sub("", t)
        if t2:
            toks.append(t2)
    return toks


def collapse_adjacent_identical(tokens: List[str]) -> List[str]:
    if not tokens:
        return tokens
    out = [tokens[0]]
    for t in tokens[1:]:
        if t != out[-1]:
            out.append(t)
    return out


# ----------------------------
# PDF extraction
# ----------------------------

def extract_pdf_lines(pdf_path: str) -> List[str]:
    try:
        import pymupdf as fitz
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
                txt = "".join(sp.get("text", "") for sp in spans if sp.get("text"))
                txt = normalize_line(txt)
                if txt:
                    lines.append(txt)
        lines.append("")

    doc.close()
    return lines


# ----------------------------
# Detection
# ----------------------------

RE_EX_START = re.compile(r"^\((\d+)\)\s*(.*)$")
RE_SUBLABEL = re.compile(r"^([a-z])\.\s*(.*)$", re.IGNORECASE)
RE_LANG_HEADER = re.compile(r"^([A-Z][^()]+?)\s*\((.+?)\)\s*$")

OPEN_TO_CLOSE = {"“": "”", "‘": "’", '"': '"', "`": "'"}
OPENERS = set(OPEN_TO_CLOSE.keys())

MAX_ITEM_LEN = 50


def has_morph_seps(s: str) -> bool:
    return "-" in s or "=" in s


def _looks_like_close_quote(text: str, i: int, ch: str) -> bool:
    if ch in {"’", "'"}:
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if nxt.isalpha():
            return False
    return True


def find_open_quote(line: str) -> Optional[Tuple[int, str]]:
    for i, ch in enumerate(line):
        if ch in OPENERS:
            return i, ch
    return None


def find_close_quote(line: str, closer: str) -> Optional[int]:
    for i, ch in enumerate(line):
        if ch == closer and _looks_like_close_quote(line, i, ch):
            return i
    return None


def extract_translation_from_lines(lines: List[str]) -> str:
    if not lines:
        return ""

    first = lines[0]
    found = find_open_quote(first)
    if not found:
        return ""

    open_i, opener = found
    closer = OPEN_TO_CLOSE[opener]

    rem = first[open_i + 1 :]
    cp = find_close_quote(rem, closer)
    if cp is not None:
        return normalize_text(rem[:cp])

    acc = rem.strip()
    for ln in lines[1:]:
        cp2 = find_close_quote(ln, closer)
        if cp2 is not None:
            return normalize_text(acc + " " + ln[:cp2])
        acc += " " + ln
    return ""


# ----------------------------
# Language line detection (weak vs strong)
# ----------------------------

RE_HAS_QUOTE = re.compile(r"[\"“”‘’`]")
RE_HAS_DIGIT = re.compile(r"\d")
RE_WEIRD_PUNCT = re.compile(r"[;:!?]")


def _all_titlecase(words: List[str]) -> bool:
    for w in words:
        if not w:
            return False
        if not w[0].isupper():
            return False
        if any(ch.isupper() for ch in w[1:]):
            return False
    return True


def is_language_line_weak(line: str) -> bool:
    line = normalize_line(line)
    if not line:
        return False
    if RE_EX_START.match(line) or RE_SUBLABEL.match(line):
        return False
    if has_morph_seps(line):
        return False
    if RE_LANG_HEADER.match(line):
        return True
    words = line.split()
    return 1 <= len(words) <= 8 and line[:1].isupper() and not line.endswith((".", "!", "?", "…"))


def is_language_line_strong(line: str) -> bool:
    line = normalize_line(line)
    if not line:
        return False
    if RE_EX_START.match(line) or RE_SUBLABEL.match(line):
        return False
    if has_morph_seps(line):
        return False
    if RE_HAS_QUOTE.search(line):
        return False
    if RE_HAS_DIGIT.search(line):
        return False
    if RE_WEIRD_PUNCT.search(line):
        return False
    if RE_LANG_HEADER.match(line):
        return True
    words = line.split()
    if not (1 <= len(words) <= 4):
        return False
    return _all_titlecase(words)


# ----------------------------
# Subexample label stripping inside content
# ----------------------------

RE_SUBLABEL_PREFIX = re.compile(r"^\s*([a-z])\.\s+", re.IGNORECASE)


def strip_leading_sublabel_from_content(lines: List[str]) -> List[str]:
    out = list(lines)
    for i, ln in enumerate(out):
        if normalize_line(ln) == "":
            continue
        if RE_SUBLABEL_PREFIX.match(ln):
            out[i] = RE_SUBLABEL_PREFIX.sub("", ln, count=1)
        break
    return out


# ----------------------------
# Reconstruction (with built-in single deletion repair)
# ----------------------------

def _drop_one_of_first_adjacent_identical_pair(raw_lines: List[str]) -> Tuple[List[str], bool]:
    normed = [normalize_line(x) for x in raw_lines]
    for i in range(len(normed) - 1):
        if normed[i] and normed[i] == normed[i + 1]:
            new_lines = list(raw_lines)
            del new_lines[i]  # drop EXACTLY one cell
            return new_lines, True
    return raw_lines, False


def _reconstruct_attempt(raw_lines: List[str]) -> Tuple[Optional[Tuple[str, str]], str]:
    raw = [normalize_line(x) for x in raw_lines]
    if not raw:
        return None, "no_between_lines"

    raw = strip_leading_sublabel_from_content(raw)

    nonempty = [x for x in raw if x.strip()]
    work = raw

    if len(work) % 2 != 0:
        work = nonempty
        if len(work) % 2 != 0:
            return None, "odd_number_of_igt_lines"

    if len(work) < 2:
        return None, "too_few_between_lines"

    half = len(work) // 2
    upper, lower = work[:half], work[half:]

    if any(len(x) > MAX_ITEM_LEN for x in upper):
        return None, "item_too_long_in_source_half"
    if any(len(x) > MAX_ITEM_LEN for x in lower):
        return None, "item_too_long_in_gloss_half"

    source = normalize_text(" ".join([x for x in upper if x.strip()]))
    gloss = normalize_text(" ".join([x for x in lower if x.strip()]))

    if not source:
        return None, "empty_source_after_join"
    if not gloss:
        return None, "empty_gloss_after_join"

    return (source, gloss), ""


def _reconstruct_core(raw_lines: List[str]) -> Tuple[Optional[Tuple[str, str]], str]:
    recon, reason = _reconstruct_attempt(raw_lines)
    if recon is not None:
        return recon, ""

    candidate = strip_leading_sublabel_from_content(raw_lines)
    repaired, changed = _drop_one_of_first_adjacent_identical_pair(candidate)
    if not changed:
        return None, reason

    recon2, reason2 = _reconstruct_attempt(repaired)
    if recon2 is not None:
        return recon2, ""

    return None, f"{reason2}|after_drop_one_of_first_adjacent_identical_pair"


def reconstruct_igt(between: List[str]) -> Tuple[Optional[Tuple[str, str]], str]:
    return _reconstruct_core(between)


# ----------------------------
# Data structures
# ----------------------------

@dataclass
class Block:
    example_id: str
    subexample_id: str
    open_line: str
    lang_line: str = ""
    inherited_lang_line: str = ""
    between: List[str] = field(default_factory=list)
    raw_between: List[str] = field(default_factory=list)
    skip_next_if_equals: str = ""  # one-shot de-dup guard


def effective_language(b: Block) -> str:
    return b.lang_line or b.inherited_lang_line


# ----------------------------
# Output helpers
# ----------------------------

def build_raw_block_lines(b: Block, translation_lines: List[str]) -> List[str]:
    out = [normalize_line(b.open_line)]
    lang = effective_language(b)
    if lang:
        out.append(normalize_line(lang))
    out.extend(b.raw_between)
    out.extend(translation_lines)
    return [normalize_line(x) for x in out if normalize_line(x)]


def report_failure(b: Block, reason: str, translation_lines: List[str], debug: bool) -> None:
    print(f"example_id: {b.example_id}")
    if b.subexample_id:
        print(f"subexample_id: {b.subexample_id}")
    print("status: failed")
    print(f"reason: {reason}")
    if debug:
        print("raw_match: [")
        for ln in build_raw_block_lines(b, translation_lines):
            print(ln)
        print("]")
    print()


def report_success(b: Block, source: str, gloss: str, translation: str) -> None:
    print(f"example_id: {b.example_id}")
    if b.subexample_id:
        print(f"subexample_id: {b.subexample_id}")
    print(f"language: {normalize_line(effective_language(b))}")
    print(f"igt: {source} || {gloss}")
    print(f"translation: {translation}")
    print()


# ----------------------------
# Finalization
# ----------------------------

def finalize_block(b: Block, translation_lines: List[str], debug: bool, require_morph_seps: bool) -> bool:
    translation_lines_n = [normalize_line(x) for x in translation_lines]
    translation = extract_translation_from_lines(translation_lines_n)
    if not translation:
        report_failure(b, "no_translation_found_within_1_to_3_lines", translation_lines_n, debug)
        return False

    recon, reason = reconstruct_igt(b.between)

    # NEW: If reconstruction fails and we had a detected lang_line, demote it and retry once.
    if not recon and b.lang_line:
        demoted_between = [b.lang_line] + list(b.between)
        recon2, reason2 = reconstruct_igt(demoted_between)
        if recon2:
            # Accept the demotion: clear local lang_line so output uses inherited language (or none).
            b.lang_line = ""
            b.between = demoted_between
            recon = recon2
            reason = ""
        else:
            reason = f"{reason}|after_demote_lang_line_then_reconstruct_failed:{reason2}"

    if not recon:
        report_failure(b, reason, translation_lines_n, debug)
        return False

    source, gloss = recon

    if require_morph_seps:
        if not has_morph_seps(source):
            report_failure(b, "source_missing_morph_separators", translation_lines_n, debug)
            return False
        if not has_morph_seps(gloss):
            report_failure(b, "gloss_missing_morph_separators", translation_lines_n, debug)
            return False

    st, gt = tokenized_words(source), tokenized_words(gloss)
    if len(st) != len(gt):
        st2, gt2 = collapse_adjacent_identical(st), collapse_adjacent_identical(gt)
        if len(st2) != len(gt2):
            report_failure(
                b,
                "token_count_mismatch_even_after_collapsing_adjacent_duplicates",
                translation_lines_n,
                debug,
            )
            return False
        source, gloss = " ".join(st2), " ".join(gt2)

    report_success(b, source, gloss, translation)
    return True


# ----------------------------
# Parser
# ----------------------------

def parse_and_stream(lines: List[str], debug: bool, require_morph_seps: bool) -> Tuple[int, int]:
    example_id: Optional[str] = None
    mother_lang = ""
    current: Optional[Block] = None

    pending: List[str] = []
    pending_closer: Optional[str] = None

    successes = 0
    total_raw_matches = 0

    def start_pending(line: str) -> None:
        nonlocal pending, pending_closer
        pending = [line]
        found = find_open_quote(line)
        pending_closer = OPEN_TO_CLOSE[found[1]] if found else None  # type: ignore[index]

    def add_content_to_current(line: str) -> None:
        assert current is not None
        ln = normalize_line(line)

        if current.skip_next_if_equals and ln and ln == current.skip_next_if_equals:
            current.skip_next_if_equals = ""
            return
        if current.skip_next_if_equals:
            current.skip_next_if_equals = ""

        current.raw_between.append(ln)
        current.between.append(ln)

    for raw in lines:
        line = normalize_line(raw)

        # Pending translation completion (allow up to 3 lines total)
        if current and pending:
            pending.append(line)
            closed = False
            if pending_closer and find_close_quote(line, pending_closer) is not None:
                closed = True
            elif extract_translation_from_lines(pending):
                closed = True

            if closed:
                total_raw_matches += 1
                if finalize_block(current, pending, debug, require_morph_seps):
                    successes += 1
                current = None
                pending = []
                pending_closer = None
                continue

            if len(pending) >= 3:
                for pl in pending:
                    add_content_to_current(pl)
                pending = []
                pending_closer = None
            continue

        # Mother opener
        m = RE_EX_START.match(line)
        if m:
            example_id = m.group(1)
            mother_lang = ""
            current = Block(example_id=example_id, subexample_id="", open_line=line)

            rest = normalize_text(m.group(2))
            if rest:
                rest_norm = normalize_line(rest)
                current.skip_next_if_equals = rest_norm
                current.raw_between.append(rest_norm)

                if not current.lang_line and is_language_line_weak(rest_norm):
                    current.lang_line = rest_norm
                    mother_lang = rest_norm
                else:
                    current.between.append(rest_norm)
            continue

        if example_id is None:
            continue

        # Subexample opener
        sm = RE_SUBLABEL.match(line)
        if sm:
            sub_id = sm.group(1).lower()
            rest = normalize_text(sm.group(2))

            current = Block(
                example_id=example_id,
                subexample_id=sub_id,
                open_line=f"{sub_id}.",
                inherited_lang_line=mother_lang,
            )

            if rest:
                rest_norm = normalize_line(rest)
                current.skip_next_if_equals = rest_norm
                current.raw_between.append(rest_norm)

                # subexample context: strict
                if not current.lang_line and is_language_line_strong(rest_norm):
                    current.lang_line = rest_norm
                else:
                    current.between.append(rest_norm)
            continue

        # Outside any block
        if current is None:
            if not mother_lang and is_language_line_weak(line):
                mother_lang = line
            continue

        # Translation start?
        if find_open_quote(line):
            start_pending(line)
            continue

        # Language line inside block?
        if not current.lang_line:
            if current.subexample_id:
                if is_language_line_strong(line):
                    current.lang_line = line
                    current.raw_between.append(line)
                    continue
            else:
                if is_language_line_weak(line):
                    current.lang_line = line
                    mother_lang = line
                    current.raw_between.append(line)
                    continue

        add_content_to_current(line)

    return successes, total_raw_matches


# ----------------------------
# Main
# ----------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--require-morph-seps", action="store_true", help="Require '-' or '=' in source+gloss (default off)")
    args = ap.parse_args()

    if not os.path.exists(args.pdf):
        print(f"ERROR: PDF not found: {args.pdf}", file=sys.stderr)
        return 2

    lines = extract_pdf_lines(args.pdf)
    successes, total = parse_and_stream(lines, args.debug, args.require_morph_seps)

    print("report:")
    print(f"extracted: {successes}")
    print(f"raw_matches: {total}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
