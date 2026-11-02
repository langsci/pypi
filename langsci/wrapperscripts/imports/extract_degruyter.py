#!/usr/bin/env python3

import argparse
import csv
import os
import re
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


CSV_FIELDS = [
    "ID", "Language_ID", "Primary_Text", "Analyzed_Word", "Gloss",
    "Translated_Text", "Meta_Language_ID", "LGR_Conformance", "Comment",
    "LGR_Conformance_Level", "Language_Name", "Abbreviations",
    "Corpus_Reference", "Source", "Contribution_ID",
]

MAX_ITEM_LEN = 50

RE_EX = re.compile(r"^\((\d+)\)\s*(.*)$")
RE_SUB = re.compile(r"^([a-z])\.\s*(.*)$", re.I)
RE_LANG_HEADER = re.compile(r"^([A-Z][^()]+?)\s*\((.+?)\)\s*$")
RE_DOI = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.I)
RE_YEAR = re.compile(r"\b(?:18|19|20)\d{2}[a-z]?\b")
RE_SOURCE_HINT = re.compile(
    r"\(([^)]*?\b(?:18|19|20)\d{2}[a-z]?(?::\s*\d+(?:[-–]\d+)?)?[^)]*?)\)"
)
RE_REF_START = re.compile(r"^References$", re.I)

MULTISPACE = re.compile(r"[ \t]+")
PUNCT_EDGE = re.compile(r"^[^\w]+|[^\w]+$")

OPEN_TO_CLOSE = {"“": "”", "‘": "’", '"': '"', "`": "'"}


def normalize_text(s: str) -> str:
    if not s:
        return ""
    return MULTISPACE.sub(" ", s.replace("\n", " ").replace("\r", " ")).strip()


def normalize_line(s: str) -> str:
    s = s.replace("\u00ad", "")
    s = s.replace("\ufb01", "fi").replace("\ufb02", "fl")
    s = s.replace("\t", " ")
    return normalize_text(s)


def tokenized_words(s: str) -> List[str]:
    out = []
    for t in normalize_text(s).split():
        t = PUNCT_EDGE.sub("", t)
        if t:
            out.append(t)
    return out


def extract_pdf_lines(pdf_path: str) -> List[str]:
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz

    doc = fitz.open(pdf_path)
    lines = []

    for page in doc:
        data = page.get_text("dict")
        for block in data.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                txt = "".join(span.get("text", "") for span in line.get("spans", []))
                txt = normalize_line(txt)
                if txt:
                    lines.append(txt)
        lines.append("")

    doc.close()
    return lines


def format_article_citation_uss(meta: dict) -> str:
    author = meta.get("author", "")
    year = meta.get("year", "")
    title = meta.get("title", "")
    journal = meta.get("journal", "")
    volume = meta.get("volume", "")
    number = meta.get("number", "")
    pages = meta.get("pages", "")
    doi = meta.get("doi", "")

    vol_issue = volume
    if number:
        vol_issue = f"{volume}({number})" if volume else f"({number})"

    parts = []
    if author:
        parts.append(f"{author}.")
    if year:
        parts.append(f"{year}.")
    if title:
        parts.append(f"{title}.")
    if journal:
        if vol_issue and pages:
            parts.append(f"{journal} {vol_issue}. {pages}.")
        elif vol_issue:
            parts.append(f"{journal} {vol_issue}.")
        else:
            parts.append(f"{journal}.")
    if doi:
        parts.append(f"doi:{doi}.")

    return normalize_text(" ".join(parts))


def extract_pdf_metadata(lines: List[str]) -> dict:
    head = [normalize_line(x) for x in lines[:120] if normalize_line(x)]
    text = " ".join(head)

    doi = ""
    m = RE_DOI.search(text)
    if m:
        doi = m.group(0).rstrip(".,;")

    author = head[0].rstrip("*") if head else ""

    title_parts = []
    for ln in head[1:10]:
        low = ln.lower()
        if "doi" in low or low.startswith("received "):
            break
        title_parts.append(ln)
    title = normalize_text(" ".join(title_parts))

    year = ""
    for ln in head:
        if "published online" in ln.lower():
            y = re.findall(r"\b(?:18|19|20)\d{2}\b", ln)
            if y:
                year = y[-1]
            break

    journal = ""
    volume = ""
    number = ""
    pages = ""

    for ln in head:
        m = re.search(r"^(.+?)\s+(\d{4});\s*(\d+)\((\d+)\):\s*([0-9]+[-–][0-9]+)", ln)
        if m:
            journal = normalize_text(m.group(1))
            year = year or m.group(2)
            volume = m.group(3)
            number = m.group(4)
            pages = m.group(5).replace("-", "–")
            break

    meta = {
        "author": author,
        "year": year,
        "title": title,
        "journal": journal,
        "volume": volume,
        "number": number,
        "pages": pages,
        "doi": doi,
    }
    meta["citation"] = format_article_citation_uss(meta)
    return meta


def find_references_section(lines: List[str]) -> List[str]:
    start = None
    for i, ln in enumerate(lines):
        if RE_REF_START.match(normalize_line(ln)):
            start = i + 1
            break
    if start is None:
        return []

    refs = []
    for ln in lines[start:]:
        ln = normalize_line(ln)
        if not ln:
            continue
        refs.append(ln)
    return refs


def build_reference_index(lines: List[str]) -> dict:
    refs = find_references_section(lines)
    entries = []
    current = []

    for ln in refs:
        if RE_YEAR.search(ln) and current:
            entries.append(normalize_text(" ".join(current)))
            current = [ln]
        else:
            current.append(ln)

    if current:
        entries.append(normalize_text(" ".join(current)))

    index = {}
    for entry in entries:
        years = RE_YEAR.findall(entry)
        if not years:
            continue
        year = years[0]

        # Surname is normally first token before comma in Unified Style references.
        surname = entry.split(",", 1)[0].strip()
        if not surname:
            continue

        key = f"{surname} {year}"
        index.setdefault(key.lower(), entry)

    return index


def extract_source_keys_from_lines(lines: List[str]) -> List[str]:
    text = " ".join(normalize_line(x) for x in lines if normalize_line(x))
    raw = RE_SOURCE_HINT.findall(text)
    keys = []

    for item in raw:
        item = normalize_text(item)
        m = re.search(r"([A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’-]+(?:\s+et\s+al\.)?)\s+((?:18|19|20)\d{2}[a-z]?)", item)
        if m:
            keys.append(f"{m.group(1)} {m.group(2)}")
        else:
            keys.append(item)

    return keys


def resolve_example_source(lines: List[str], ref_index: dict, article_meta: dict) -> str:
    keys = extract_source_keys_from_lines(lines)
    pdf_citation = article_meta.get("citation", "")

    if not keys:
        return pdf_citation

    resolved = []
    for key in keys:
        lookup = key.lower()

        if lookup in ref_index:
            precise = ref_index[lookup]
        else:
            m = re.search(r"([A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’-]+).*?((?:18|19|20)\d{2}[a-z]?)", key)
            if m:
                short = f"{m.group(1)} {m.group(2)}"
                precise = ref_index.get(short.lower(), key)
            else:
                precise = key

        if pdf_citation:
            resolved.append(f"{precise} via {pdf_citation}")
        else:
            resolved.append(precise)

    return "; ".join(dict.fromkeys(resolved))

def find_open_quote(line):
    for i, c in enumerate(line):
        if c in OPEN_TO_CLOSE:
            return i, c
    return None


def find_close_quote(line, closer):
    for i, c in enumerate(line):
        if c == closer:
            if c in ("'", "’") and i + 1 < len(line) and line[i + 1].isalpha():
                continue
            return i
    return None


def extract_translation(lines):
    if not lines:
        return ""

    found = find_open_quote(lines[0])
    if not found:
        return ""

    i, opener = found
    closer = OPEN_TO_CLOSE[opener]

    rest = lines[0][i + 1:]
    cp = find_close_quote(rest, closer)
    if cp is not None:
        return normalize_text(rest[:cp])

    acc = rest
    for ln in lines[1:]:
        cp = find_close_quote(ln, closer)
        if cp is not None:
            return normalize_text(acc + " " + ln[:cp])
        acc += " " + ln

    return ""


def drop_duplicate_cell(lines):
    norm = [normalize_line(x) for x in lines]
    for i in range(len(norm) - 1):
        if norm[i] and norm[i] == norm[i + 1]:
            new = list(lines)
            del new[i]
            return new, True
    return lines, False


def reconstruct(lines):
    raw = [normalize_line(x) for x in lines if normalize_line(x)]

    if len(raw) % 2 != 0:
        raw2, changed = drop_duplicate_cell(raw)
        if changed:
            raw = raw2
        else:
            return None

    if len(raw) < 2:
        return None

    half = len(raw) // 2
    upper, lower = raw[:half], raw[half:]

    if any(len(x) > MAX_ITEM_LEN for x in upper + lower):
        return None

    return normalize_text(" ".join(upper)), normalize_text(" ".join(lower))


def detect_language(line):
    line = normalize_line(line)

    m = RE_LANG_HEADER.match(line)
    if m:
        return normalize_text(m.group(1))

    words = line.split()
    if 1 <= len(words) <= 4 and all(w[:1].isupper() for w in words):
        if not any(ch in line for ch in "-=;:!?0123456789"):
            return line

    return ""


@dataclass
class Block:
    example_id: str
    sub_id: str
    lang: str = ""
    inherited_lang: str = ""
    between: List[str] = field(default_factory=list)
    raw: List[str] = field(default_factory=list)


def effective_lang(b):
    return b.lang or b.inherited_lang or "Unknown"


def make_row(idx, b, src, gls, tr, source_ref):
    return {
        "ID": f"exgpt-{idx}",
        "Language_ID": "unknown",
        "Primary_Text": src,
        "Analyzed_Word": "\t".join(tokenized_words(src)),
        "Gloss": "\t".join(tokenized_words(gls)),
        "Translated_Text": tr,
        "Meta_Language_ID": "stan1293",
        "LGR_Conformance": "",
        "Comment": "",
        "LGR_Conformance_Level": "2",
        "Language_Name": effective_lang(b),
        "Abbreviations": "{}",
        "Corpus_Reference": "",
        "Source": source_ref,
        "Contribution_ID": "extracted",
    }


def parse(lines, article_meta, ref_index):
    example_id = None
    mother_lang = ""
    current = None
    pending = []
    closer = None

    rows = []
    total = 0

    for line in lines:
        line = normalize_line(line)

        if current and pending:
            pending.append(line)
            if closer and find_close_quote(line, closer) is not None:
                total += 1

                translation = extract_translation(pending)
                rec = reconstruct(current.between)

                if not rec and current.lang:
                    rec = reconstruct([current.lang] + current.between)
                    if rec:
                        current.lang = ""

                if rec and translation:
                    src, gls = rec
                    source_ref = resolve_example_source(current.raw + pending, ref_index, article_meta)
                    rows.append(make_row(len(rows) + 1, current, src, gls, translation, source_ref))

                current = None
                pending = []
                closer = None
                continue

            if len(pending) >= 3:
                current.raw.extend(pending)
                current.between.extend(pending)
                pending = []
                closer = None
                continue

        m = RE_EX.match(line)
        if m:
            example_id = m.group(1)
            current = Block(example_id, "")

            rest = normalize_text(m.group(2))
            if rest:
                current.raw.append(rest)
                lang = detect_language(rest)
                if lang:
                    current.lang = lang
                    mother_lang = lang
                else:
                    current.between.append(rest)
            continue

        if example_id:
            sm = RE_SUB.match(line)
            if sm:
                current = Block(example_id, sm.group(1).lower(), inherited_lang=mother_lang)

                rest = normalize_text(sm.group(2))
                if rest:
                    current.raw.append(rest)
                    lang = detect_language(rest)
                    if lang:
                        current.lang = lang
                    else:
                        current.between.append(rest)
                continue

        if not current:
            if example_id:
                lang = detect_language(line)
                if lang:
                    mother_lang = lang
            continue

        q = find_open_quote(line)
        if q:
            pending = [line]
            closer = OPEN_TO_CLOSE[q[1]]
            continue

        current.raw.append(line)

        if not current.lang:
            lang = detect_language(line)
            if lang:
                current.lang = lang
                if not current.sub_id:
                    mother_lang = lang
                continue

        current.between.append(line)

    return rows, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--out", default="-")
    args = ap.parse_args()

    if not os.path.exists(args.pdf):
        print("PDF not found", file=sys.stderr)
        return 1

    lines = extract_pdf_lines(args.pdf)
    article_meta = extract_pdf_metadata(lines)
    ref_index = build_reference_index(lines)
    rows, total = parse(lines, article_meta, ref_index)

    out = sys.stdout if args.out == "-" else open(args.out, "w", encoding="utf-8", newline="")
    with out:
        writer = csv.DictWriter(out, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"report: extracted {len(rows)} / {total}", file=sys.stderr)


if __name__ == "__main__":
    main()
