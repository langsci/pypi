#!/usr/bin/env python3
# -*- coding: utf-8 -*-

r"""
Extract interlinear linguistic examples from a PDF and emit CSV rows following
an ExGPT/CLDF-style template.

Design principles:
- trust explicit example numbering over visual layout
- trust short, less-than-full-line strings immediately preceding examples as language labels
- emit CSV rows only for examples with a recoverable \gll-style source/gloss pair
- skip suspicious cases conservatively and record the reason in a sidecar log
- extract article-level provenance and per-example source citations

Usage:
    python extract_examples_gb4e_csv.py input.pdf -o examples.csv
    python extract_examples_gb4e_csv.py input.pdf -o examples.csv --tex examples.tex --json debug.json
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

try:
    import fitz  # PyMuPDF
except ImportError:
    print("This script requires PyMuPDF. Install it with: pip install pymupdf", file=sys.stderr)
    raise


TEMPLATE_COLUMNS = [
    "ID",
    "Language_ID",
    "Primary_Text",
    "Analyzed_Word",
    "Gloss",
    "Translated_Text",
    "Meta_Language_ID",
    "LGR_Conformance",
    "Comment",
    "LGR_Conformance_Level",
    "Language_Name",
    "Abbreviations",
    "Corpus_Reference",
    "Source",
    "Contribution_ID",
]

DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.I)
LICENSE_PATTERNS = [
    re.compile(r"\bCC BY 4\.0\b", re.I),
    re.compile(r"\bCreative Commons\b", re.I),
    re.compile(r"\blicense\b", re.I),
]

HEADER_PATTERNS = [
    re.compile(r"^Guest \(guest\) IP: .* On: .*$"),
    re.compile(r"^Studies in Language ISSN .*?$"),
    re.compile(r"^Available under the CC BY .*?$"),
    re.compile(r"^https?://doi\.org/.*?$"),
]

SECTIONISH_PATTERNS = [
    re.compile(r"^\d+\.\s+[A-Z]"),
    re.compile(r"^\d+\.\d+\s+[A-Z]"),
    re.compile(r"^Table \d+\."),
    re.compile(r"^Figure \d+\."),
    re.compile(r"^References$"),
    re.compile(r"^Funding$"),
    re.compile(r"^Acknowledgments$"),
    re.compile(r"^Abbreviations$"),
]

PAGE_MARK_RE = re.compile(r"^<PARSED TEXT FOR PAGE: \d+ / \d+>$")
FOOTNOTE_RE = re.compile(r"^\d+\.\s")

EXAMPLE_START_RE = re.compile(
    r"^\((?P<num>\d+)\)\s*(?:(?P<sub>[a-z])\.\s*)?(?P<rest>.*)$"
)
SUBEXAMPLE_START_RE = re.compile(r"^(?P<sub>[a-z])\.\s*(?P<rest>.*)$")

TRANSLATION_RE = re.compile(r"^[‘'\"“].+[’'”\"]\s*$")
SAME_LINE_SOURCE_RE = re.compile(
    r"""
    ^(?P<trans>[‘'\"“].+[’'”\"])
    \s*
    (?P<source>\([^()]*?\b\d{4}\b[^()]*\))
    \s*$
    """,
    re.VERBOSE,
)
PAREN_SOURCE_RE = re.compile(r"^\((?P<source>[^()]*?\b\d{4}\b[^()]*)\)\s*$")
BARE_SOURCE_RE = re.compile(r"^(?P<source>[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’.-]+(?:\s+&\s+[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’.-]+)?\s+\d{4}[:;,].+)$")

ARTICLE_LINE_RE = re.compile(
    r"(?P<journal>[A-Z][A-Za-z& .\-]+?)\s+"
    r"(?P<volume>\d+)"
    r"(?:(?:[:(])(?P<issue>\d+)[)]?)?"
    r"\s*\((?P<year>\d{4})\),\s*"
    r"(?:pp\.\s*)?(?P<pages>\d+\s*[–-]\s*\d+)"
)
PUBLISHED_RE = re.compile(r"Published online:\s+\d{1,2}\s+[A-Za-z]+\s+(?P<year>\d{4})")
REF_KEY_RE = re.compile(r"(?P<surname>[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’.-]+).*?\b(?P<year>\d{4}[a-z]?)\b")


@dataclass
class ArticleInfo:
    metadata: Dict[str, str]
    author: Optional[str]
    title: Optional[str]
    year: Optional[str]
    journal: Optional[str]
    volume: Optional[str]
    issue: Optional[str]
    pages: Optional[str]
    doi: Optional[str]
    license_text: Optional[str]
    citation: str


@dataclass
class Example:
    number: str
    subletter: Optional[str]
    source_page: int
    language: Optional[str]
    language_method: Optional[str]
    raw_lines: List[str]
    object_line: Optional[str]
    gloss_line: Optional[str]
    translation: Optional[str]
    precise_source_key: Optional[str]
    resolved_source: Optional[str]
    skipped: bool = False
    skip_reason: Optional[str] = None

    @property
    def label(self) -> str:
        return f"{self.number}{self.subletter or ''}"


@dataclass
class RunLog:
    language_counts: Dict[str, int]
    language_method_counts: Dict[str, int]
    source_key_count: int
    resolved_source_count: int
    missing_language_count: int
    kept_count: int
    skipped_count: int


# ---------------------------------------------------------------------------
# Normalization and low-level helpers
# ---------------------------------------------------------------------------


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u00ad", "")
    text = text.replace("\ufeff", "")
    text = text.replace("￾", "")
    return text


def clean_metadata_value(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = normalize_text(value).strip()
    return value or None


def strip_empty(lines: List[str]) -> List[str]:
    out = lines[:]
    while out and not out[0]:
        out.pop(0)
    while out and not out[-1]:
        out.pop()
    return out


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for src, tgt in replacements.items():
        text = text.replace(src, tgt)
    return text


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def word_count(text: str) -> int:
    return len([w for w in text.split() if w])


# ---------------------------------------------------------------------------
# PDF extraction and article-level metadata
# ---------------------------------------------------------------------------


def clean_page_text(text: str) -> List[str]:
    text = normalize_text(text)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    raw_lines = [line.rstrip() for line in text.splitlines()]
    lines: List[str] = []

    for line in raw_lines:
        line = line.strip()
        if not line:
            lines.append("")
            continue
        if PAGE_MARK_RE.match(line):
            continue
        if any(p.match(line) for p in HEADER_PATTERNS):
            continue
        if re.fullmatch(r"\[\d+\]", line):
            continue
        lines.append(line)

    return lines


def extract_pdf_lines(pdf_path: Path) -> Tuple[List[Tuple[int, str]], ArticleInfo, str]:
    doc = fitz.open(pdf_path)

    lines_with_pages: List[Tuple[int, str]] = []
    first_pages: List[str] = []
    full_pages: List[str] = []

    for page_idx, page in enumerate(doc, start=1):
        text = page.get_text("text")
        full_pages.append(text)
        if page_idx <= 3:
            first_pages.append(text)
        for line in clean_page_text(text):
            lines_with_pages.append((page_idx, line))

    article_info = extract_article_info(doc, "\n".join(first_pages), lines_with_pages)
    return lines_with_pages, article_info, "\n".join(full_pages)


def extract_article_info(doc: fitz.Document, first_pages_text: str, lines_with_pages: List[Tuple[int, str]]) -> ArticleInfo:
    meta = {k: clean_metadata_value(v) or "" for k, v in (doc.metadata or {}).items()}
    first_text = normalize_text(first_pages_text)

    doi = None
    for candidate in [meta.get("subject", ""), meta.get("title", ""), meta.get("keywords", ""), first_text]:
        m = DOI_RE.search(candidate or "")
        if m:
            doi = m.group(0).rstrip(".")
            break

    license_text = None
    for candidate in [meta.get("subject", ""), meta.get("keywords", ""), first_text]:
        for pat in LICENSE_PATTERNS:
            m = pat.search(candidate or "")
            if m:
                license_text = "CC BY 4.0" if re.search(r"\bCC BY 4\.0\b", candidate, re.I) else m.group(0)
                break
        if license_text:
            break

    title = clean_metadata_value(meta.get("title"))
    author = clean_metadata_value(meta.get("author"))
    year = None
    journal = None
    volume = None
    issue = None
    pages = None

    for line in first_text.splitlines():
        m = ARTICLE_LINE_RE.search(normalize_space(line))
        if m:
            journal = normalize_space(m.group("journal"))
            volume = m.group("volume")
            issue = m.group("issue")
            pages = normalize_space(m.group("pages")).replace(" - ", "–").replace("-", "–")
            year = m.group("year")
            break

    if year is None:
        m = PUBLISHED_RE.search(first_text)
        if m:
            year = m.group("year")

    if title is None or author is None:
        guessed_title, guessed_author = guess_title_author_from_first_page(lines_with_pages)
        title = title or guessed_title
        author = author or guessed_author

    citation = format_unified_style_citation(
        author=author,
        title=title,
        year=year,
        journal=journal,
        volume=volume,
        issue=issue,
        pages=pages,
        doi=doi,
    )

    return ArticleInfo(
        metadata=meta,
        author=author,
        title=title,
        year=year,
        journal=journal,
        volume=volume,
        issue=issue,
        pages=pages,
        doi=doi,
        license_text=license_text,
        citation=citation,
    )


def guess_title_author_from_first_page(lines_with_pages: List[Tuple[int, str]]) -> Tuple[Optional[str], Optional[str]]:
    page1 = [line for page, line in lines_with_pages if page == 1 and line.strip()]
    page1 = [line for line in page1 if not DOI_RE.search(line) and not line.startswith("https://")]
    if not page1:
        return None, None

    # Conservative guess: title is the first one or two lines before a line that looks like authors.
    title_lines: List[str] = []
    author_lines: List[str] = []
    for line in page1[:10]:
        if re.search(r"\b(University|Universität|CNRS|Institute|College)\b", line):
            break
        if title_lines and ("," in line or " and " in line or re.search(r"\d", line)):
            author_lines.append(line)
        elif not author_lines:
            title_lines.append(line)
        else:
            author_lines.append(line)

    title = normalize_space(" ".join(title_lines[:3])) or None
    author = normalize_space(" ".join(author_lines[:3])) or None
    return title, author


def format_unified_style_citation(
    author: Optional[str],
    title: Optional[str],
    year: Optional[str],
    journal: Optional[str],
    volume: Optional[str],
    issue: Optional[str],
    pages: Optional[str],
    doi: Optional[str],
) -> str:
    parts: List[str] = []
    parts.append((author or "Unknown author").rstrip("."))
    parts.append((year or "n.d.").rstrip("."))
    parts.append((title or "Untitled").rstrip("."))

    journal_part = ""
    if journal:
        journal_part = journal.rstrip(".")
        if volume:
            journal_part += f" {volume}"
            if issue:
                journal_part += f"({issue})"
        if pages:
            journal_part += f". {pages}"
    if journal_part:
        parts.append(journal_part.rstrip("."))

    citation = ". ".join(parts).rstrip(".") + "."
    if doi:
        citation += f" doi:{doi}."
    return citation


# ---------------------------------------------------------------------------
# References and source resolution
# ---------------------------------------------------------------------------


def extract_references_entries(full_text: str) -> List[str]:
    text = normalize_text(full_text)
    m = re.search(r"(?m)^References\s*$", text)
    if not m:
        return []

    refs_text = text[m.end():]
    refs_text = re.split(r"(?m)^(Appendix|Appendices|Author queries|Funding|Acknowledgments)\b", refs_text)[0]
    raw_lines = [normalize_space(line) for line in refs_text.splitlines()]
    raw_lines = [line for line in raw_lines if line]

    entries: List[str] = []
    current: List[str] = []

    start_re = re.compile(r"^[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’.-]+,\s+.*\b\d{4}[a-z]?\b")
    for line in raw_lines:
        if start_re.match(line) and current:
            entries.append(normalize_space(" ".join(current)))
            current = [line]
        else:
            current.append(line)
    if current:
        entries.append(normalize_space(" ".join(current)))

    return entries


def resolve_source_key(source_key: Optional[str], references: List[str]) -> Optional[str]:
    if not source_key:
        return None

    key = source_key.strip().strip("()")
    m = REF_KEY_RE.search(key)
    if not m:
        return None

    surname = m.group("surname")
    year = m.group("year")
    year_base = year[:4]

    candidates = []
    for entry in references:
        if re.search(rf"\b{re.escape(surname)}\b", entry) and re.search(rf"\b{re.escape(year_base)}[a-z]?\b", entry):
            candidates.append(entry)

    if not candidates:
        return None

    # Prefer the shortest plausible full entry if there are duplicates caused by parsing noise.
    candidates.sort(key=len)
    return candidates[0]


# ---------------------------------------------------------------------------
# Language label detection
# ---------------------------------------------------------------------------


def looks_like_language_label_line(text: str) -> bool:
    """
    Identify possible language labels structurally.

    A language label is expected to be the non-empty line immediately before
    an example number and to be shorter than a normal full prose line. This
    deliberately avoids whitelists and typography checks, because PDFs often
    lose bold/small-caps information.

    The cutoff below operationalizes "less than a full line". It is generous
    enough for multi-word names such as "Mandarin Chinese" or "Jakarta
    Indonesian", while rejecting ordinary prose lines.
    """
    text = text.strip()
    if not text:
        return False
    if EXAMPLE_START_RE.match(text):
        return False

    # "Less than a full line": most extracted prose lines in the target PDFs
    # are substantially longer than this.
    if len(text) > 60:
        return False

    if re.search(r"\d", text):
        return False
    if re.search(r"[.!?:;]$", text):
        return False

    words = text.split()
    if not words:
        return False

    # Allow language-name-like words, including hyphens, apostrophes, periods,
    # and parenthesized labels/codes that sometimes occur with language names.
    if not all(re.match(r"^[A-Za-zÀ-ÖØ-öø-ÿ'’().-]+$", w) for w in words):
        return False

    # Avoid obvious non-language structural headings.
    if text.lower() in {"references", "funding", "acknowledgments", "abbreviations"}:
        return False

    return True

def detect_pre_example_language(lines_with_pages: List[Tuple[int, str]]) -> Dict[Tuple[int, int], str]:
    page_lines: Dict[int, List[str]] = {}
    for page, line in lines_with_pages:
        page_lines.setdefault(page, []).append(line)

    result: Dict[Tuple[int, int], str] = {}
    for page, lines in page_lines.items():
        for idx, line in enumerate(lines):
            if not EXAMPLE_START_RE.match(line):
                continue
            prev_idx = idx - 1
            while prev_idx >= 0 and not lines[prev_idx].strip():
                prev_idx -= 1
            if prev_idx < 0:
                continue
            prev_line = lines[prev_idx].strip()
            if looks_like_language_label_line(prev_line):
                result[(page, idx)] = prev_line
    return result


def choose_language(page: int, line_index_in_page: int, pre_example_lang: Dict[Tuple[int, int], str]) -> Tuple[Optional[str], Optional[str]]:
    if (page, line_index_in_page) in pre_example_lang:
        return pre_example_lang[(page, line_index_in_page)], "short_preceding_line"
    return None, None


# ---------------------------------------------------------------------------
# Example segmentation
# ---------------------------------------------------------------------------


def looks_like_boundary(line: str) -> bool:
    if not line:
        return False
    if any(p.match(line) for p in SECTIONISH_PATTERNS):
        return True
    if FOOTNOTE_RE.match(line):
        return True
    return False


def plausible_example_number(num: int, prev_num: Optional[int]) -> Tuple[bool, Optional[str]]:
    if num > 1800:
        return False, "number > 1800, almost certainly a year"
    if num > 200:
        return False, "number > 200, unlikely to be an example number"
    if prev_num is not None and abs(num - prev_num) > 5:
        return False, f"number jump too large relative to previous example ({prev_num} -> {num})"
    return True, None


def split_examples(
    lines_with_pages: List[Tuple[int, str]],
    pre_example_lang: Dict[Tuple[int, int], str],
) -> List[Tuple[str, Optional[str], int, Optional[str], Optional[str], List[str], bool, Optional[str]]]:
    blocks = []

    current_num: Optional[str] = None
    current_sub: Optional[str] = None
    current_page: Optional[int] = None
    current_lang: Optional[str] = None
    current_lang_method: Optional[str] = None
    current_lines: List[str] = []

    last_plausible_num: Optional[int] = None
    page_line_counter: Dict[int, int] = {}

    def flush(pre_skipped: bool = False, pre_skip_reason: Optional[str] = None) -> None:
        nonlocal current_num, current_sub, current_page, current_lang, current_lang_method, current_lines
        if current_num is not None:
            blocks.append((
                current_num,
                current_sub,
                current_page or 0,
                current_lang,
                current_lang_method,
                current_lines[:],
                pre_skipped,
                pre_skip_reason,
            ))
        current_num = None
        current_sub = None
        current_page = None
        current_lang = None
        current_lang_method = None
        current_lines = []

    i = 0
    while i < len(lines_with_pages):
        page, line = lines_with_pages[i]
        page_line_counter[page] = page_line_counter.get(page, 0) + 1
        line_index_in_page = page_line_counter[page] - 1

        m = EXAMPLE_START_RE.match(line)
        if not m:
            i += 1
            continue

        num = int(m.group("num"))
        ok, reason = plausible_example_number(num, last_plausible_num)

        flush()

        current_num = m.group("num")
        current_sub = m.group("sub")
        current_page = page
        current_lang, current_lang_method = choose_language(page, line_index_in_page, pre_example_lang)
        rest = m.group("rest").strip()
        current_lines = [rest] if rest else []

        i += 1
        while i < len(lines_with_pages):
            next_page, next_line = lines_with_pages[i]

            if EXAMPLE_START_RE.match(next_line):
                break

            subm = SUBEXAMPLE_START_RE.match(next_line)
            if subm and current_num is not None:
                inherited_num = current_num
                inherited_lang = current_lang
                inherited_lang_method = current_lang_method or "inherited_mother_example"
                flush(pre_skipped=not ok, pre_skip_reason=reason)
                current_num = inherited_num
                current_sub = subm.group("sub")
                current_page = next_page
                current_lang = inherited_lang
                current_lang_method = inherited_lang_method
                sub_rest = subm.group("rest").strip()
                current_lines = [sub_rest] if sub_rest else []
                i += 1
                continue

            if looks_like_boundary(next_line):
                if current_lines and any(
                    TRANSLATION_RE.match(x) or SAME_LINE_SOURCE_RE.match(x) or PAREN_SOURCE_RE.match(x) or BARE_SOURCE_RE.match(x)
                    for x in current_lines
                ):
                    break

            current_lines.append(next_line)
            i += 1

        flush(pre_skipped=not ok, pre_skip_reason=reason)

        if ok:
            last_plausible_num = num

    flush()
    return blocks


# ---------------------------------------------------------------------------
# Parsing example internals
# ---------------------------------------------------------------------------


def clean_translation(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    text = text.strip().strip("“”‘’\"'")
    return text


def extract_translation_and_source(lines: List[str]) -> Tuple[List[str], Optional[str], Optional[str]]:
    lines = strip_empty(lines)
    trans_idx = None
    translation = None
    source_key = None

    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        same = SAME_LINE_SOURCE_RE.match(line)
        if same:
            trans_idx = i
            translation = same.group("trans")
            source_key = same.group("source").strip().strip("()")
            break
        if TRANSLATION_RE.match(line):
            trans_idx = i
            translation = line
            break

    if trans_idx is None:
        return lines, None, None

    trailing = [ln.strip() for ln in lines[trans_idx + 1:] if ln.strip()]
    for candidate in trailing[:3]:
        par = PAREN_SOURCE_RE.match(candidate)
        bare = BARE_SOURCE_RE.match(candidate)
        if par:
            source_key = par.group("source").strip()
            break
        if bare:
            source_key = bare.group("source").strip()
            break

    return lines[:trans_idx], clean_translation(translation), source_key


def is_noise(line: str) -> bool:
    if not line:
        return True
    if looks_like_boundary(line):
        return True
    if re.match(r"^\([A-Za-z].*\d{4}.*\)$", line):
        return True
    if re.match(r"^\[[^\]]+\]$", line):
        return True
    if re.search(r"\b(adapted|elicited)\b", line, flags=re.I):
        return True
    if re.match(r"^[A-Z][a-z]+ \(\d{4}\)", line):
        return True
    return False


def pair_interlinear_tokens(lines: List[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    core = [ln for ln in strip_empty(lines) if not is_noise(ln)]

    if len(core) < 2:
        return None, None, "too few candidate lines for \\gll"
    if len(core) % 2 != 0:
        return None, None, "odd number of candidate lines, cannot pair object/gloss safely"

    obj_parts: List[str] = []
    gloss_parts: List[str] = []
    for i in range(0, len(core), 2):
        obj_parts.append(core[i])
        gloss_parts.append(core[i + 1])

    object_line = normalize_space(" ".join(obj_parts))
    gloss_line = normalize_space(" ".join(gloss_parts))

    if not object_line or not gloss_line:
        return None, None, "empty object or gloss line after pairing"
    if len(object_line) > 200:
        return None, None, "source-language line > 200 chars, treated as erroneous"

    obj_wc = word_count(object_line)
    gloss_wc = word_count(gloss_line)
    if obj_wc != gloss_wc:
        return None, None, f"source/gloss word-count mismatch ({obj_wc} vs. {gloss_wc})"

    return object_line, gloss_line, None


def parse_block(
    number: str,
    subletter: Optional[str],
    page: int,
    language: Optional[str],
    language_method: Optional[str],
    raw_lines: List[str],
    pre_skipped: bool,
    pre_skip_reason: Optional[str],
    references: List[str],
) -> Example:
    lines = strip_empty(raw_lines)

    if pre_skipped:
        return Example(number, subletter, page, language, language_method, raw_lines, None, None, None, None, None, True, pre_skip_reason)

    body, translation, precise_source_key = extract_translation_and_source(lines)
    object_line, gloss_line, parse_reason = pair_interlinear_tokens(body)
    resolved_source = resolve_source_key(precise_source_key, references) if precise_source_key else None

    if object_line is None or gloss_line is None:
        return Example(
            number=number,
            subletter=subletter,
            source_page=page,
            language=language,
            language_method=language_method,
            raw_lines=raw_lines,
            object_line=None,
            gloss_line=None,
            translation=translation,
            precise_source_key=precise_source_key,
            resolved_source=resolved_source,
            skipped=True,
            skip_reason=parse_reason or "could not recover \\gll",
        )

    return Example(
        number=number,
        subletter=subletter,
        source_page=page,
        language=language,
        language_method=language_method,
        raw_lines=raw_lines,
        object_line=object_line,
        gloss_line=gloss_line,
        translation=translation,
        precise_source_key=precise_source_key,
        resolved_source=resolved_source,
        skipped=False,
        skip_reason=None,
    )


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------


def infer_abbreviations(gloss_line: str) -> Dict[str, Optional[str]]:
    abbreviations: Dict[str, Optional[str]] = {}
    for token in re.split(r"\s+", gloss_line):
        # Split common morpheme separators but retain items such as 1SG, PST, DOM.
        for part in re.split(r"[-.=:/]", token):
            part = part.strip("[](){}.,;!?‘’'\"")
            if not part:
                continue
            if re.fullmatch(r"[A-Z][A-Z0-9]+", part) or re.fullmatch(r"\d[A-Z]+", part):
                abbreviations.setdefault(part, None)
    return abbreviations


def source_for_row(ex: Example, article_citation: str) -> str:
    if ex.precise_source_key:
        precise = ex.resolved_source if ex.resolved_source else ex.precise_source_key
        return f"{precise} via {article_citation}"
    return article_citation


def example_to_csv_row(ex: Example, article_info: ArticleInfo, contribution_id: str, row_index: int) -> Dict[str, str]:
    analyzed = "\t".join(ex.object_line.split()) if ex.object_line else ""
    gloss = "\t".join(ex.gloss_line.split()) if ex.gloss_line else ""
    primary = ex.object_line or ""
    abbreviations = infer_abbreviations(ex.gloss_line or "")

    return {
        "ID": f"{contribution_id}-{row_index}",
        "Language_ID": "",
        "Primary_Text": primary,
        "Analyzed_Word": analyzed,
        "Gloss": gloss,
        "Translated_Text": ex.translation or "",
        "Meta_Language_ID": "stan1293",
        "LGR_Conformance": "",
        "Comment": f"PDF example {ex.label}, page {ex.source_page}",
        "LGR_Conformance_Level": "2",
        "Language_Name": ex.language or "",
        "Abbreviations": json.dumps(abbreviations, ensure_ascii=False, sort_keys=True),
        "Corpus_Reference": ex.precise_source_key or "",
        "Source": source_for_row(ex, article_info.citation),
        "Contribution_ID": contribution_id,
    }


def write_csv(examples: List[Example], article_info: ArticleInfo, output: Path, contribution_id: str) -> None:
    kept = [ex for ex in examples if not ex.skipped]
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TEMPLATE_COLUMNS)
        writer.writeheader()
        for idx, ex in enumerate(kept, start=1):
            writer.writerow(example_to_csv_row(ex, article_info, contribution_id, idx))


def write_skip_log(examples: List[Example], output: Path) -> None:
    lines = []
    for ex in examples:
        if ex.skipped:
            lines.append(f"skipped example {ex.label}: {ex.skip_reason or 'skipped'}")
    output.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


# ---------------------------------------------------------------------------
# Optional LaTeX output
# ---------------------------------------------------------------------------


def latex_comment_block(ex: Example) -> List[str]:
    return [f"% skipped example {ex.label}: {ex.skip_reason or 'skipped'}", ""]


def latex_for_single_example(ex: Example) -> List[str]:
    out = [f"% example {ex.label}, page {ex.source_page}"]
    out.append(r"\ea")
    source = f"[{ex.language}] {ex.object_line}" if ex.language else (ex.object_line or "")
    out.append(r"\gll " + latex_escape(source) + r" \\")
    out.append(latex_escape(ex.gloss_line or "") + r" \\")
    if ex.translation:
        out.append(r"\glt `" + latex_escape(ex.translation) + r"'")
    if ex.precise_source_key:
        out.append(f"% source: {ex.resolved_source or ex.precise_source_key}")
    out.append(r"\z")
    out.append("")
    return out


def write_tex(examples: List[Example], article_info: ArticleInfo, run_log: RunLog, output: Path) -> None:
    out = [
        r"\documentclass{article}",
        r"\usepackage{langsci-gb4e}",
        r"\noautomath",
        "% Source PDF metadata",
        f"% article citation: {article_info.citation}",
    ]
    if article_info.license_text:
        out.append(f"% license: {article_info.license_text}")
    out.extend([
        "% Extraction log",
        f"% languages identified: {sum(run_log.language_counts.values())}",
        f"% unique languages identified: {len(run_log.language_counts)}",
        f"% source keys identified: {run_log.source_key_count}",
        f"% source keys resolved: {run_log.resolved_source_count}",
        r"\begin{document}",
        "",
    ])
    for ex in examples:
        if ex.skipped:
            out.extend(latex_comment_block(ex))
        else:
            out.extend(latex_for_single_example(ex))
    out.append(r"\end{document}")
    output.write_text("\n".join(out) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Logging and CLI
# ---------------------------------------------------------------------------


def build_run_log(examples: List[Example]) -> RunLog:
    language_counts = Counter()
    language_method_counts = Counter()
    source_key_count = 0
    resolved_source_count = 0
    missing_language_count = 0
    kept_count = 0
    skipped_count = 0

    for ex in examples:
        if ex.skipped:
            skipped_count += 1
        else:
            kept_count += 1
        if ex.language:
            language_counts[ex.language] += 1
        else:
            missing_language_count += 1
        if ex.language_method:
            language_method_counts[ex.language_method] += 1
        if ex.precise_source_key:
            source_key_count += 1
        if ex.resolved_source:
            resolved_source_count += 1

    return RunLog(
        language_counts=dict(language_counts),
        language_method_counts=dict(language_method_counts),
        source_key_count=source_key_count,
        resolved_source_count=resolved_source_count,
        missing_language_count=missing_language_count,
        kept_count=kept_count,
        skipped_count=skipped_count,
    )


def default_contribution_id(pdf_path: Path) -> str:
    stem = re.sub(r"[^A-Za-z0-9]+", "-", pdf_path.stem).strip("-").lower()
    return stem or "extracted"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path, help="Input PDF")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output CSV file")
    parser.add_argument("--tex", type=Path, help="Optional LaTeX output")
    parser.add_argument("--json", type=Path, help="Optional debug JSON output")
    parser.add_argument("--log", type=Path, help="Optional skip-log output; defaults to <output>.skips.log")
    parser.add_argument("--contribution-id", help="Contribution_ID value; defaults to sanitized PDF stem")
    args = parser.parse_args()

    lines_with_pages, article_info, full_text = extract_pdf_lines(args.pdf)
    references = extract_references_entries(full_text)
    pre_example_lang = detect_pre_example_language(lines_with_pages)
    raw_blocks = split_examples(lines_with_pages, pre_example_lang)

    examples = [
        parse_block(num, sub, page, lang, lang_method, lines, pre_skipped, pre_skip_reason, references)
        for num, sub, page, lang, lang_method, lines, pre_skipped, pre_skip_reason in raw_blocks
    ]
    run_log = build_run_log(examples)
    contribution_id = args.contribution_id or default_contribution_id(args.pdf)

    write_csv(examples, article_info, args.output, contribution_id)
    skip_log_path = args.log or args.output.with_suffix(args.output.suffix + ".skips.log")
    write_skip_log(examples, skip_log_path)

    if args.tex:
        write_tex(examples, article_info, run_log, args.tex)

    if args.json:
        payload = {
            "article_info": asdict(article_info),
            "reference_count": len(references),
            "pre_example_lang": {f"{page}:{idx}": lang for (page, idx), lang in pre_example_lang.items()},
            "run_log": asdict(run_log),
            "examples": [asdict(ex) for ex in examples],
        }
        args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote CSV: {args.output}")
    print(f"Wrote skip log: {skip_log_path}")
    if args.tex:
        print(f"Wrote LaTeX: {args.tex}")
    if args.json:
        print(f"Wrote JSON: {args.json}")
    print(f"Article citation: {article_info.citation}")
    print(f"Processed {len(examples)} candidate example blocks")
    print(f"Kept {run_log.kept_count} with recoverable source/gloss pairs")
    print(f"Skipped {run_log.skipped_count}")
    print("\n=== LANGUAGE LOG ===")
    print(f"Languages identified: {sum(run_log.language_counts.values())}")
    print(f"Unique languages: {len(run_log.language_counts)}")
    print(f"Examples without language: {run_log.missing_language_count}")
    for lang, count in sorted(run_log.language_counts.items()):
        print(f"  {lang}: {count}")
    print("\n=== SOURCE LOG ===")
    print(f"Precise source keys identified: {run_log.source_key_count}")
    print(f"Precise source keys resolved: {run_log.resolved_source_count}")
    print(f"Reference entries parsed: {len(references)}")


if __name__ == "__main__":
    main()
