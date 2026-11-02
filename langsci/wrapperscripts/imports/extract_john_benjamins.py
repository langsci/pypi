#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import fitz  # PyMuPDF
except ImportError:
    print("This script requires PyMuPDF: pip install pymupdf", file=sys.stderr)
    raise


LANGUAGE_NAMES = {"Spanish", "Romanian", "Bulgarian", "Tima", "Yali"}
SMALLCAPS_FONT_HINTS = ("smallcaps", "small-caps", ".sc", "_sc", "sc-", "caps")
BOLD_FONT_HINTS = ("bold", "black", "heavy", "demi", "semibold")
LICENSE_PATTERNS = [
    re.compile(r"CC BY 4\.0", re.I),
    re.compile(r"Creative Commons", re.I),
    re.compile(r"license", re.I),
]
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.I)

HEADER_PATTERNS = [
    re.compile(r"^Guest \(guest\) IP: .* On: .*?$"),
    re.compile(r"^DAM and discourse prominence \[\d+\]$"),
    re.compile(r"^\[\d+\] Paul Compensis et al\.$"),
    re.compile(r"^Studies in Language ISSN .*?$"),
    re.compile(r"^Available under the CC BY .*?$"),
    re.compile(r"^https?://doi\.org/.*?$"),
]

SECTIONISH_PATTERNS = [
    re.compile(r"^\d+\.\s+[A-Z]"),
    re.compile(r"^\d+\.\d+\s+[A-Z]"),
    re.compile(r"^Table \d+\."),
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
TRANSLATION_RE = re.compile(r"^[‘'\"“].+[’'”\"]\s*(?:\([^)]*\))?$")

# Optional bibliographic source after translation, e.g.:
# ‘text’ (Smith 2000: 123)
# 'text' (Hill & Mardale 2019: 20)
SOURCE_CITATION_RE = re.compile(
    r"""
    ^(?P<trans>[‘'\"“].+[’'”\"])
    \s*
    (?P<source>
        \(
            [^()]*?
            \b[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’.-]+
            [^()]*?
            \b\d{4}
            (?::\s*\d+(?:[–-]\d+)?)?
            [^()]*?
        \)
    )\s*$
    """,
    re.VERBOSE,
)


@dataclass
class SpanInfo:
    page: int
    text: str
    font: str
    size: float
    bbox: Tuple[float, float, float, float]
    line_no: int


@dataclass
class PdfInfo:
    metadata: Dict[str, str]
    title: Optional[str]
    author: Optional[str]
    subject: Optional[str]
    keywords: Optional[str]
    creator: Optional[str]
    producer: Optional[str]
    creation_date: Optional[str]
    mod_date: Optional[str]
    doi: Optional[str]
    license_text: Optional[str]


@dataclass
class Example:
    number: str
    subletter: Optional[str]
    source_page: int
    language: Optional[str]
    raw_lines: List[str]
    object_line: Optional[str]
    gloss_line: Optional[str]
    translation: Optional[str]
    source_citation: Optional[str]
    skipped: bool = False
    skip_reason: Optional[str] = None

    @property
    def label(self) -> str:
        return f"{self.number}{self.subletter or ''}"


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u00ad", "")
    text = text.replace("\ufeff", "")
    text = text.replace("￾", "")
    return text


def latex_escape(s: str) -> str:
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
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s


def clean_page_text(text: str) -> List[str]:
    text = normalize_text(text)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    raw_lines = [ln.rstrip() for ln in text.splitlines()]
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


def clean_metadata_value(v: Optional[str]) -> Optional[str]:
    if not v:
        return None
    v = normalize_text(v).strip()
    return v or None


def extract_pdf_info(doc: fitz.Document, first_pages_text: str) -> PdfInfo:
    meta = {k: clean_metadata_value(v) or "" for k, v in (doc.metadata or {}).items()}

    doi = None
    for candidate in [
        meta.get("subject", ""),
        meta.get("title", ""),
        meta.get("keywords", ""),
        first_pages_text,
    ]:
        m = DOI_RE.search(candidate or "")
        if m:
            doi = m.group(0)
            break

    license_text = None
    for candidate in [
        meta.get("subject", ""),
        meta.get("keywords", ""),
        first_pages_text,
    ]:
        for pat in LICENSE_PATTERNS:
            m = pat.search(candidate or "")
            if m:
                if "CC BY 4.0" in candidate:
                    license_text = "CC BY 4.0"
                else:
                    license_text = m.group(0)
                break
        if license_text:
            break

    return PdfInfo(
        metadata=meta,
        title=clean_metadata_value(meta.get("title")),
        author=clean_metadata_value(meta.get("author")),
        subject=clean_metadata_value(meta.get("subject")),
        keywords=clean_metadata_value(meta.get("keywords")),
        creator=clean_metadata_value(meta.get("creator")),
        producer=clean_metadata_value(meta.get("producer")),
        creation_date=clean_metadata_value(meta.get("creationDate")),
        mod_date=clean_metadata_value(meta.get("modDate")),
        doi=doi,
        license_text=license_text,
    )


def span_text_is_smallcaps_candidate(text: str, font: str) -> bool:
    t = text.strip()
    if not t:
        return False

    font_l = (font or "").lower()
    if any(h in font_l for h in SMALLCAPS_FONT_HINTS):
        return True

    letters = [c for c in t if c.isalpha()]
    if not letters:
        return False
    upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    if len(t.split()) <= 2 and 0.6 <= upper_ratio <= 1.0 and len(t) <= 20:
        normalized = t.title()
        if normalized in LANGUAGE_NAMES:
            return True

    return False


def font_is_bold(font: str) -> bool:
    font_l = (font or "").lower()
    return any(h in font_l for h in BOLD_FONT_HINTS)


def looks_like_bold_lang_line(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    if EXAMPLE_START_RE.match(t):
        return False
    words = t.split()
    if not (1 <= len(words) <= 3):
        return False
    if re.search(r"[.!?:;]$", t):
        return False
    if re.search(r"\d", t):
        return False
    if not all(re.match(r"^[A-Za-zÀ-ÖØ-öø-ÿ'’.-]+$", w) for w in words):
        return False
    return True


def collect_span_info(doc: fitz.Document) -> List[SpanInfo]:
    spans: List[SpanInfo] = []
    for page_idx, page in enumerate(doc, start=1):
        data = page.get_text("dict")
        line_counter = 0
        for block in data.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                line_counter += 1
                for span in line.get("spans", []):
                    text = normalize_text(span.get("text", "")).strip()
                    if not text:
                        continue
                    spans.append(
                        SpanInfo(
                            page=page_idx,
                            text=text,
                            font=span.get("font", "") or "",
                            size=float(span.get("size", 0.0) or 0.0),
                            bbox=tuple(span.get("bbox", (0, 0, 0, 0))),
                            line_no=line_counter,
                        )
                    )
    return spans


def detect_smallcaps_language_candidates(spans: List[SpanInfo]) -> Dict[int, List[str]]:
    out: Dict[int, List[str]] = {}
    for sp in spans:
        if not span_text_is_smallcaps_candidate(sp.text, sp.font):
            continue
        label = sp.text.strip().title()
        if label in LANGUAGE_NAMES:
            out.setdefault(sp.page, []).append(label)
    return out


def detect_bold_pre_example_language(lines_with_pages: List[Tuple[int, str]], spans: List[SpanInfo]) -> Dict[Tuple[int, int], str]:
    """
    Map (page, line_index_in_page_of_example_start) -> language label
    when previous non-empty line is 1-3 bold words.
    """
    # Build per-page line font summaries from spans
    page_line_fonts: Dict[Tuple[int, int], List[SpanInfo]] = {}
    for sp in spans:
        page_line_fonts.setdefault((sp.page, sp.line_no), []).append(sp)

    # Recreate page-local cleaned lines with indices
    page_lines: Dict[int, List[str]] = {}
    for page, line in lines_with_pages:
        page_lines.setdefault(page, []).append(line)

    result: Dict[Tuple[int, int], str] = {}

    for page, lines in page_lines.items():
        # naive alignment: cleaned page line order against extracted line_no order
        # good enough for the immediately-preceding-line heuristic
        for idx, line in enumerate(lines):
            if not EXAMPLE_START_RE.match(line):
                continue

            prev_idx = idx - 1
            while prev_idx >= 0 and not lines[prev_idx].strip():
                prev_idx -= 1
            if prev_idx < 0:
                continue

            prev_line = lines[prev_idx].strip()
            if not looks_like_bold_lang_line(prev_line):
                continue

            # map cleaned line index to nearest span line index, 1-based
            span_infos = page_line_fonts.get((page, prev_idx + 1), [])
            if not span_infos:
                continue

            bold_spans = [sp for sp in span_infos if font_is_bold(sp.font)]
            joined_span_text = " ".join(sp.text for sp in span_infos).strip()

            # require all or almost all visible content on that line to be bold
            if not bold_spans:
                continue

            if normalize_text(joined_span_text).strip() != normalize_text(prev_line).strip():
                # still allow if the visible span text contains the cleaned line
                if normalize_text(prev_line).strip() not in normalize_text(joined_span_text).strip():
                    continue

            label = prev_line.title()
            result[(page, idx)] = label

    return result


def extract_pdf_lines_and_layout(pdf_path: Path) -> Tuple[
    List[Tuple[int, str]],
    Dict[int, List[str]],
    Dict[Tuple[int, int], str],
    PdfInfo,
]:
    doc = fitz.open(pdf_path)

    all_lines: List[Tuple[int, str]] = []
    first_pages_text_parts: List[str] = []
    for page_idx, page in enumerate(doc, start=1):
        text = page.get_text("text")
        if page_idx <= 3:
            first_pages_text_parts.append(text)
        for line in clean_page_text(text):
            all_lines.append((page_idx, line))

    spans = collect_span_info(doc)
    smallcaps_candidates = detect_smallcaps_language_candidates(spans)
    bold_pre_example_lang = detect_bold_pre_example_language(all_lines, spans)
    pdf_info = extract_pdf_info(doc, "\n".join(first_pages_text_parts))

    return all_lines, smallcaps_candidates, bold_pre_example_lang, pdf_info


def looks_like_boundary(line: str) -> bool:
    if not line:
        return False
    if any(p.match(line) for p in SECTIONISH_PATTERNS):
        return True
    if line in LANGUAGE_NAMES:
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


def choose_language(
    explicit_heading_lang: Optional[str],
    page: int,
    line_index_in_page: int,
    smallcaps_candidates: Dict[int, List[str]],
    bold_pre_example_lang: Dict[Tuple[int, int], str],
) -> Optional[str]:
    # Highest priority: bold 1-3 word line immediately preceding example number
    if (page, line_index_in_page) in bold_pre_example_lang:
        return bold_pre_example_lang[(page, line_index_in_page)]

    if explicit_heading_lang in LANGUAGE_NAMES:
        return explicit_heading_lang

    cands = smallcaps_candidates.get(page, [])
    if not cands:
        return None
    for c in cands:
        if c in LANGUAGE_NAMES:
            return c
    return None


def split_examples(
    lines_with_pages: List[Tuple[int, str]],
    smallcaps_candidates: Dict[int, List[str]],
    bold_pre_example_lang: Dict[Tuple[int, int], str],
) -> List[Tuple[str, Optional[str], int, Optional[str], List[str], bool, Optional[str]]]:
    blocks: List[Tuple[str, Optional[str], int, Optional[str], List[str], bool, Optional[str]]] = []

    current_num: Optional[str] = None
    current_sub: Optional[str] = None
    current_page: Optional[int] = None
    current_lang: Optional[str] = None
    current_lines: List[str] = []

    last_seen_language: Optional[str] = None
    last_plausible_num: Optional[int] = None

    # page-local line indices
    page_line_counter: Dict[int, int] = {}

    def flush(pre_skipped: bool = False, pre_skip_reason: Optional[str] = None) -> None:
        nonlocal current_num, current_sub, current_page, current_lang, current_lines
        if current_num is not None:
            blocks.append((
                current_num,
                current_sub,
                current_page or 0,
                current_lang,
                current_lines[:],
                pre_skipped,
                pre_skip_reason,
            ))
        current_num = None
        current_sub = None
        current_page = None
        current_lang = None
        current_lines = []

    i = 0
    while i < len(lines_with_pages):
        page, line = lines_with_pages[i]
        page_line_counter[page] = page_line_counter.get(page, 0) + 1
        line_index_in_page = page_line_counter[page] - 1  # zero-based

        if line in LANGUAGE_NAMES:
            last_seen_language = line
            i += 1
            continue

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
        current_lang = choose_language(
            last_seen_language,
            page,
            line_index_in_page,
            smallcaps_candidates,
            bold_pre_example_lang,
        )
        current_lines = [m.group("rest").strip()] if m.group("rest").strip() else []

        i += 1
        while i < len(lines_with_pages):
            _, next_line = lines_with_pages[i]

            if next_line in LANGUAGE_NAMES:
                break
            if EXAMPLE_START_RE.match(next_line):
                break

            subm = SUBEXAMPLE_START_RE.match(next_line)
            if subm and current_num is not None and current_sub is not None:
                break

            if looks_like_boundary(next_line):
                if current_lines and any(TRANSLATION_RE.match(x) for x in current_lines):
                    break

            current_lines.append(next_line)
            i += 1

        flush(pre_skipped=not ok, pre_skip_reason=reason)

        if ok:
            last_plausible_num = num

        continue

    flush()
    return blocks


def strip_empty(lines: List[str]) -> List[str]:
    out = lines[:]
    while out and not out[0]:
        out.pop(0)
    while out and not out[-1]:
        out.pop()
    return out


def clean_translation(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = s.strip().strip("“”‘’\"'")
    return latex_escape(s)


def split_translation_and_source(line: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if line is None:
        return None, None
    m = SOURCE_CITATION_RE.match(line.strip())
    if m:
        trans = m.group("trans")
        source = m.group("source")
        return trans, source
    return line, None


def extract_translation(lines: List[str]) -> Tuple[List[str], Optional[str], Optional[str]]:
    idx = None
    for i in range(len(lines) - 1, -1, -1):
        if TRANSLATION_RE.match(lines[i]) or SOURCE_CITATION_RE.match(lines[i]):
            idx = i
            break
    if idx is None:
        return lines, None, None

    raw_translation = lines[idx]
    trans, source = split_translation_and_source(raw_translation)
    return lines[:idx], trans, source


def is_noise(line: str) -> bool:
    if not line:
        return True
    if looks_like_boundary(line):
        return True
    if line in LANGUAGE_NAMES:
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


def word_count(s: str) -> int:
    return len([w for w in s.split() if w])


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

    object_line = re.sub(r"\s+", " ", " ".join(obj_parts)).strip()
    gloss_line = re.sub(r"\s+", " ", " ".join(gloss_parts)).strip()

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
    raw_lines: List[str],
    pre_skipped: bool,
    pre_skip_reason: Optional[str],
) -> Example:
    lines = strip_empty(raw_lines)

    if pre_skipped:
        return Example(
            number=number,
            subletter=subletter,
            source_page=page,
            language=language,
            raw_lines=raw_lines,
            object_line=None,
            gloss_line=None,
            translation=None,
            source_citation=None,
            skipped=True,
            skip_reason=pre_skip_reason,
        )

    body, translation, source_citation = extract_translation(lines)
    object_line, gloss_line, parse_reason = pair_interlinear_tokens(body)

    if object_line is None or gloss_line is None:
        return Example(
            number=number,
            subletter=subletter,
            source_page=page,
            language=language,
            raw_lines=raw_lines,
            object_line=None,
            gloss_line=None,
            translation=clean_translation(translation),
            source_citation=source_citation,
            skipped=True,
            skip_reason=parse_reason or "could not recover \\gll",
        )

    if language:
        object_line = f"[{language}] {object_line}"

    return Example(
        number=number,
        subletter=subletter,
        source_page=page,
        language=language,
        raw_lines=raw_lines,
        object_line=object_line,
        gloss_line=gloss_line,
        translation=clean_translation(translation),
        source_citation=source_citation,
        skipped=False,
        skip_reason=None,
    )


def latex_comment_block(ex: Example) -> List[str]:
    reason = ex.skip_reason or "skipped"
    return [f"% skipped example {ex.label}: {reason}", ""]


def latex_source_comment(source_citation: Optional[str]) -> List[str]:
    if not source_citation:
        return []
    return [f"% source: {source_citation}"]


def latex_for_single_example(ex: Example) -> List[str]:
    out = [f"% example {ex.label}, page {ex.source_page}"]
    out.append(r"\ea")
    out.append(r"\gll " + latex_escape(ex.object_line or "") + r" \\")
    out.append(latex_escape(ex.gloss_line or "") + r" \\")
    if ex.translation:
        out.append(r"\glt `" + ex.translation + r"'")
    out.extend(latex_source_comment(ex.source_citation))
    out.append(r"\z")
    out.append("")
    return out


def latex_for_xlist_group(group: List[Example]) -> List[str]:
    out = [f"% grouped example {group[0].number}", r"\ea", r"\begin{xlist}"]
    for ex in group:
        if ex.skipped:
            out.extend(latex_comment_block(ex))
            continue
        out.append(r"\ex")
        out.append(r"\gll " + latex_escape(ex.object_line or "") + r" \\")
        out.append(latex_escape(ex.gloss_line or "") + r" \\")
        if ex.translation:
            out.append(r"\glt `" + ex.translation + r"'")
        out.extend(latex_source_comment(ex.source_citation))
        out.append("")
    out.append(r"\end{xlist}")
    out.append(r"\z")
    out.append("")
    return out


def build_metadata_preamble(pdf_info: PdfInfo) -> List[str]:
    out: List[str] = []

    out.append("% Source PDF metadata")
    for key in ["title", "author", "subject", "keywords", "creator", "producer", "creationDate", "modDate"]:
        value = pdf_info.metadata.get(key, "")
        if value:
            out.append(f"% {key}: {value}")

    if pdf_info.doi:
        out.append(f"% doi: {pdf_info.doi}")
    if pdf_info.license_text:
        out.append(f"% license: {pdf_info.license_text}")

    out.append(r"\usepackage{hyperref}")

    pdf_title = latex_escape(pdf_info.title or "")
    pdf_author = latex_escape(pdf_info.author or "")
    pdf_subject_parts = []
    if pdf_info.subject:
        pdf_subject_parts.append(pdf_info.subject)
    if pdf_info.doi:
        pdf_subject_parts.append(f"DOI: {pdf_info.doi}")
    if pdf_info.license_text:
        pdf_subject_parts.append(f"License: {pdf_info.license_text}")
    pdf_subject = latex_escape(" | ".join(pdf_subject_parts))
    pdf_keywords = latex_escape(pdf_info.keywords or "")

    out.append(
        r"\hypersetup{"
        + f"pdftitle={{{pdf_title}}},"
        + f"pdfauthor={{{pdf_author}}},"
        + f"pdfsubject={{{pdf_subject}}},"
        + f"pdfkeywords={{{pdf_keywords}}}"
        + r"}"
    )
    out.append("")
    return out


def wrap_latex_document(examples: List[Example], pdf_info: PdfInfo) -> str:
    out: List[str] = [
        r"\documentclass{article}",
        r"\usepackage{langsci-gb4e}",
        r"\noautomath",
    ]

    out.extend(build_metadata_preamble(pdf_info))
    out.append(r"\begin{document}")
    out.append("")

    i = 0
    while i < len(examples):
        ex = examples[i]

        if ex.subletter is not None:
            group = [ex]
            j = i + 1
            while j < len(examples) and examples[j].number == ex.number and examples[j].subletter is not None:
                group.append(examples[j])
                j += 1
            out.extend(latex_for_xlist_group(group))
            i = j
            continue

        if ex.skipped:
            out.extend(latex_comment_block(ex))
        else:
            out.extend(latex_for_single_example(ex))

        i += 1

    out.append(r"\end{document}")
    out.append("")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path, help="Input PDF")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output .tex file")
    parser.add_argument("--json", type=Path, help="Optional debug JSON output")
    args = parser.parse_args()

    lines_with_pages, smallcaps_candidates, bold_pre_example_lang, pdf_info = extract_pdf_lines_and_layout(args.pdf)

    raw_blocks = split_examples(
        lines_with_pages,
        smallcaps_candidates,
        bold_pre_example_lang,
    )

    examples = [
        parse_block(num, sub, page, lang, lines, pre_skipped, pre_skip_reason)
        for num, sub, page, lang, lines, pre_skipped, pre_skip_reason in raw_blocks
    ]

    tex = wrap_latex_document(examples, pdf_info)
    args.output.write_text(tex, encoding="utf-8")

    if args.json:
        payload = {
            "pdf_info": asdict(pdf_info),
            "smallcaps_candidates": smallcaps_candidates,
            "bold_pre_example_lang": {f"{k[0]}:{k[1]}": v for k, v in bold_pre_example_lang.items()},
            "examples": [asdict(ex) for ex in examples],
        }
        args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    n_total = len(examples)
    n_kept = sum(1 for e in examples if not e.skipped)
    n_skipped = n_total - n_kept

    print(f"Wrote {args.output}")
    if args.json:
        print(f"Wrote {args.json}")
    print(f"Processed {n_total} example blocks")
    print(f"Kept {n_kept} with recoverable \\gll")
    print(f"Skipped {n_skipped}")


if __name__ == "__main__":
    main()
