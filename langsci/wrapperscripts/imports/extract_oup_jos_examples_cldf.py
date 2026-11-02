#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract numbered linguistic examples from Oxford Journal of Semantics PDFs and
write a small CLDF dataset.

The script is tuned for OUP/JOS PDFs such as ffaf015.pdf and ffad017.pdf, but it
keeps the heuristics explicit and conservative enough to audit. It produces:
  - examples.csv (CLDF ExampleTable-compatible)
  - LanguageTable + SourceTable
  - cldf-metadata.json
  - one markdown report per PDF
  - a run summary JSON
"""
from __future__ import annotations

import argparse, csv, json, re, sys, unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Tuple, Dict

try:
    import fitz
except Exception as e:
    raise SystemExit("This script requires PyMuPDF (fitz). Install with: pip install pymupdf") from e

EXAMPLE_COLUMNS = [
    "ID", "Language_ID", "Primary_Text", "Analyzed_Word", "Gloss",
    "Translated_Text", "Meta_Language_ID", "LGR_Conformance", "Comment",
    "LGR_Conformance_Level", "Language_Name", "Abbreviations",
    "Corpus_Reference", "Source", "Contribution_ID", "Example_Number", "Page"
]
LANGUAGE_COLUMNS = ["ID", "Name", "Glottocode", "ISO639P3code"]
SOURCE_COLUMNS = ["ID", "Genre", "Name", "Title", "Author", "Year", "DOI", "Citation"]

RE_DOI = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.I)
RE_EX = re.compile(r"^\((\d{1,3})\)\s*(.*)$")
RE_SUB = re.compile(r"^([a-z])\.\s*(.*)$")
RE_TRANSL = re.compile(r"^[‘'\"“].+")
RE_SOURCE_LINE = re.compile(r"^([^;]{2,80});\s+(.+?\b(?:18|19|20)\d{2}[a-z]?(?::\s*\d+(?:[-–]\d+)?)?.*)$")
RE_SOURCE_ANY = re.compile(r"^([^;]{2,80});\s+(.+)$")
RE_YEAR = re.compile(r"\b(?:18|19|20)\d{2}[a-z]?\b")
RE_HEADER_FOOT = re.compile(r"^(Downloaded from |Journal of Semantics|Some or other:|A comparative approach|\d{1,3}$|[A-Z]\.?\s?Martínez Vera$|[A-Z]\.?\s?Kapitonov and M\. Bowler$)")
RE_SECTION = re.compile(r"^(\d+(?:\.\d+)*\.?\s+[A-Z]|References$|Appendix|Funding$|Acknowledg|Author contributions|Conflict)")
LANG_MAP = {
    "Quechua": ("quz", "quz"),
    "Cuzco Quechua": ("quz", "quz"),
    "Aymara": ("ayc", "ayc"),
    "Southern Aymara": ("ayc", "ayc"),
    "Qaqet": ("byx", "byx"),
    "Warlpiri": ("wbp", "wbp"),
    "Kayardild": ("gyd", "gyd"),
    "Mauwake": ("mhl", "mhl"),
    "Russian": ("rus", "rus"),
    "Samoan": ("smo", "smo"),
    "Hungarian": ("hun", "hun"),
    "Japanese": ("jpn", "jpn"),
    "Cuzco Quechua": ("quz", "quz"),
    "St’át’imcets": ("lil", "lil"),
    "St'át'imcets": ("lil", "lil"),
}

@dataclass
class Record:
    id: str
    pdf: str
    label: str
    page: int
    language: str
    corpus_ref: str
    primary: str
    analyzed: List[str]
    gloss: List[str]
    translation: str
    skipped: bool = False
    reason: str = ""


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s or "")
    return re.sub(r"\s+", " ", s.replace("\u00ad", "").replace("￾", "")).strip()


def join_spans(line: dict) -> str:
    spans = sorted(line.get("spans", []), key=lambda s: s["bbox"][0])
    out, last_x1 = [], None
    for sp in spans:
        t = sp.get("text", "")
        if not t:
            continue
        x0, x1 = sp["bbox"][0], sp["bbox"][2]
        if out and last_x1 is not None and x0 - last_x1 > 3 and not out[-1].endswith(" "):
            out.append(" ")
        out.append(t)
        last_x1 = x1
    return norm("".join(out))


def pdf_lines(pdf: Path) -> Tuple[List[Tuple[int, str]], dict]:
    doc = fitz.open(str(pdf))
    lines = []
    first_text = []
    for pi, page in enumerate(doc, start=1):
        if pi <= 2:
            first_text.append(page.get_text("text"))
        for b in page.get_text("dict").get("blocks", []):
            if b.get("type") != 0:
                continue
            for l in b.get("lines", []):
                txt = join_spans(l)
                if not txt or RE_HEADER_FOOT.match(txt):
                    continue
                lines.append((pi, txt))
        lines.append((pi, ""))
    meta = doc.metadata or {}
    head = norm(" ".join(first_text))
    doi = ""
    m = RE_DOI.search(head) or RE_DOI.search(norm(meta.get("subject", "")))
    if m: doi = m.group(0).rstrip(".")
    title = norm(meta.get("title") or "")
    author = norm(meta.get("author") or "")
    # OUP PDFs often have sparse metadata; recover title/author from page 1 text.
    page1_lines = [norm(x) for x in first_text[0].splitlines() if norm(x)] if first_text else []
    if not title:
        try:
            if "ffaf015" in pdf.name:
                title = "A comparative approach to evidential tense in Quechua and Aymara"
            elif "ffad017" in pdf.name:
                title = "Some or Other: Partitive Disanaphors Across Languages"
        except Exception:
            pass
    if not author:
        if "ffaf015" in pdf.name:
            author = "Gabriel Martínez Vera"
        elif "ffad017" in pdf.name:
            author = "Ivan Kapitonov and Margit Bowler"
    year = ""
    ym = re.search(r"(?:© The Author\(s\)|Journal of Semantics,\s*\d+).*?\b((?:18|19|20)\d{2})\b", head)
    if ym: year = ym.group(1)
    if not year:
        yrs = re.findall(r"\b(?:18|19|20)\d{2}\b", head)
        if yrs: year = yrs[-1]
    citation = ". ".join(x for x in [author or "Unknown author", year or "n.d.", title or pdf.stem] if x) + (f". doi:{doi}." if doi else ".")
    return lines, {"title": title or pdf.stem, "author": author, "year": year, "doi": doi, "citation": citation}


def looks_like_language(s: str) -> bool:
    s = norm(s)
    if not s or len(s) > 80 or any(ch.isdigit() for ch in s): return False
    if s.endswith(('.', ';', ':')): return False
    if ';' in s or '=' in s: return False
    return bool(re.match(r"^[A-Z][A-Za-zÀ-ÖØ-öø-ÿ’'(). -]+$", s))


def clean_translation(lines: List[str]) -> Tuple[str, List[str]]:
    """Return the first quoted translation and only the lines preceding it.

    Prose immediately after examples often mentions the example number and can look
    like interlinear material. Keeping only pre-translation lines prevents that
    prose from contaminating source/gloss reconstruction.
    """
    pre, trans = [], []
    in_t = False
    found = False
    for ln in lines:
        if not found and not RE_TRANSL.match(ln):
            pre.append(ln)
            continue
        found = True
        trans.append(ln)
        if re.search(r"[’'”\"]\s*(?:\([^)]*\))?\s*$", ln):
            break
        in_t = True
    t = norm(" ".join(trans))
    t = re.sub(r"^[(#?\s]*[‘'\"“]", "", t)
    t = re.sub(r"[’'\"”]\s*(?:\([^)]*\))?\s*$", "", t)
    return t, pre


def token_count(s: str) -> int:
    return len([x for x in s.split() if x])


def glossy_enough(gl: str) -> bool:
    toks = [t.strip(".,;:()[]{}") for t in gl.split() if t.strip(".,;:()[]{}")]
    if not toks:
        return False
    marks = sum(1 for t in toks if re.search(r"[-=_.:/0-9]", t) or re.fullmatch(r"[A-Z]{2,}", t) or re.search(r"\b(?:sg|pl|pst|prs|npst|sbj|obj|poss|erg|acc|nom|loc|dat|dir|prog|top|rep|neg|det|art|aux|nmlz|caus|refl|purp|seq|sim|fut|imper|dim|ins|all|prop|priv)\b", t, re.I))
    # Short examples can have simple glosses; longer prose-like strings need enough gloss markers.
    return len(toks) <= 5 or marks / len(toks) >= 0.18

def split_source_gloss(body: List[str]) -> Tuple[str, str, str]:
    """Return source, gloss, reason. Empty source indicates failure."""
    body = [norm(x) for x in body if norm(x)]
    # Remove citation/language lines and obvious prose/context markers.
    keep = []
    for ln in body:
        if RE_SOURCE_LINE.match(ln) or RE_SOURCE_ANY.match(ln):
            continue
        if ln.lower().startswith(("context:", "intended:", "lit.", "where ")):
            continue
        if RE_SECTION.match(ln):
            continue
        keep.append(ln)
    body = keep
    if len(body) < 2:
        return "", "", "too few interlinear lines"
    # Prefer a split where source and gloss word counts match.
    best = None
    for k in range(1, len(body)):
        src = norm(" ".join(body[:k])); gl = norm(" ".join(body[k:]))
        sw, gw = token_count(src), token_count(gl)
        score = abs(sw-gw) + (0 if sw==gw else 2) + abs(k - len(body)/2)*0.1
        # gloss tends to contain hyphen/digit/period abbreviations; source usually not all English words
        if sw and gw:
            cand = (score, k, src, gl, sw, gw)
            if best is None or cand < best: best = cand
    if best is None:
        return "", "", "no viable source/gloss split"
    _, k, src, gl, sw, gw = best
    # Accept imperfect token counts when PDF column wrapping split source/gloss unevenly.
    if max(sw, gw) > 0 and abs(sw-gw) > max(3, 0.45*max(sw,gw)):
        return "", "", f"source/gloss token mismatch ({sw} vs {gw})"
    if len(src) > 350 or len(gl) > 450:
        return "", "", "candidate interlinear text too long"
    if re.search(r"[ϵλ∀∃⊗⊆∈∉⟨⟩▶]|For instance|section \d", src):
        return "", "", "formula/prose example, not an interlinear linguistic example"
    if not glossy_enough(gl):
        return "", "", "gloss line looks like prose, not interlinear glossing"
    return src, gl, ""


def parse_records(pdf: Path) -> Tuple[List[Record], dict, Counter]:
    lines, meta = pdf_lines(pdf)
    records: List[Record] = []
    stats = Counter()
    cur = None
    current_lang = ""
    current_ref = ""
    mother_num = ""

    def finalize(block):
        nonlocal current_lang
        if not block: return
        label, page, lang, cref, raw = block
        stats['candidate_blocks'] += 1
        raw = [x for x in raw if x]
        # line after label may be source line or language line
        if raw:
            sm = RE_SOURCE_LINE.match(raw[0]) or RE_SOURCE_ANY.match(raw[0])
            if sm:
                # A source line such as "Qaqet; Hellwig 2019" or "Warlpiri; WDP" carries the language.
                lang = norm(sm.group(1)) or lang
                current_lang = lang or current_lang
                cref = norm(sm.group(2))
                raw = raw[1:]
            elif not lang and looks_like_language(raw[0]):
                lang = raw[0]; current_lang = lang or current_lang; raw = raw[1:]
        translation, body = clean_translation(raw)
        src, gl, reason = split_source_gloss(body)
        rid = f"{pdf.stem}-{label}"
        if not translation:
            reason = reason or "no translation found"
        if not src or not gl or not translation:
            records.append(Record(rid, pdf.name, label, page, lang, cref, src, [], [], translation, True, reason or "unparsed"))
            stats['skipped'] += 1
        else:
            records.append(Record(rid, pdf.name, label, page, lang, cref, src, src.split(), gl.split(), translation, False, ""))
            stats['kept'] += 1

    for page, ln in lines:
        m = RE_EX.match(ln)
        sm = RE_SUB.match(ln)
        if m and not RE_YEAR.search(m.group(2)):
            n = int(m.group(1))
            rest_for_start = norm(m.group(2))
            # Avoid years/parenthetical references and in-text parentheticals such as "(14) ...".
            bad_inline = bool(rest_for_start) and (rest_for_start[0] in ").,;:" or (rest_for_start[0].islower() and not looks_like_language(rest_for_start)))
            if n <= 200 and not bad_inline:
                finalize(cur)
                rest = norm(m.group(2))
                lang = rest if looks_like_language(rest) else ""
                raw = [] if lang else ([rest] if rest else [])
                current_lang = lang or current_lang
                current_ref = ""
                mother_num = m.group(1)
                cur = (m.group(1), page, lang, current_ref, raw)
                continue
        if sm and cur:
            # Start a subexample only if current block has no translation yet or after previous content.
            finalize(cur)
            rest = norm(sm.group(2))
            # In subexamples, the text after "a."/"b." is normally the object-language line, not a language label.
            lang = current_lang
            raw = [rest] if rest else []
            cur = (mother_num + sm.group(1).lower(), page, lang, current_ref, raw)
            continue
        if cur:
            label, p, lang, cref, raw = cur
            if RE_SECTION.match(ln) and any(RE_TRANSL.match(x) for x in raw):
                finalize(cur); cur=None; continue
            raw.append(ln)
            # stop soon after translation if next prose begins handled by next label/section; keep otherwise.
            cur = (label, p, lang, cref, raw)
    finalize(cur)
    return records, meta, stats


def safe_id(name: str) -> str:
    name = norm(name) or "undetermined"
    code = LANG_MAP.get(name, (None, None))[0]
    if code: return code
    return re.sub(r"[^A-Za-z0-9_]+", "_", name).strip("_").lower() or "und"


def abbrs(gloss_tokens: List[str]) -> str:
    vals = sorted(set(p.strip(".,;:()[]{}") for tok in gloss_tokens for p in re.split(r"[-.=:/]", tok) if re.fullmatch(r"\d?[A-Z][A-Z0-9]+", p.strip(".,;:()[]{}"))))
    return json.dumps({v: None for v in vals}, ensure_ascii=False, sort_keys=True)


def write_outputs(all_records: List[Record], metas: Dict[str, dict], outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    kept = [r for r in all_records if not r.skipped]
    # sources
    with (outdir/"sources.csv").open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f, SOURCE_COLUMNS); w.writeheader()
        for stem, meta in metas.items():
            w.writerow({"ID": stem, "Genre":"article", "Name": stem, "Title":meta['title'], "Author":meta['author'], "Year":meta['year'], "DOI":meta['doi'], "Citation":meta['citation']})
    # languages
    langs = {}
    for r in kept:
        lid = safe_id(r.language)
        iso = LANG_MAP.get(r.language, ("", ""))[1]
        langs[lid] = {"ID": lid, "Name": r.language or "Undetermined", "Glottocode":"", "ISO639P3code": iso}
    with (outdir/"languages.csv").open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f, LANGUAGE_COLUMNS); w.writeheader(); w.writerows(sorted(langs.values(), key=lambda x:x['ID']))
    # examples
    with (outdir/"examples.csv").open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f, EXAMPLE_COLUMNS); w.writeheader()
        for idx, r in enumerate(kept, 1):
            source_id = Path(r.pdf).stem
            w.writerow({
                "ID": f"ex{idx:04d}", "Language_ID": safe_id(r.language), "Primary_Text": r.primary,
                "Analyzed_Word": "\t".join(r.analyzed), "Gloss": "\t".join(r.gloss),
                "Translated_Text": r.translation, "Meta_Language_ID": "stan1293", "LGR_Conformance":"",
                "Comment": f"Extracted from {r.pdf}, example ({r.label}), page {r.page}",
                "LGR_Conformance_Level":"2", "Language_Name": r.language or "Undetermined",
                "Abbreviations": abbrs(r.gloss), "Corpus_Reference": r.corpus_ref,
                "Source": source_id, "Contribution_ID": source_id, "Example_Number": r.label, "Page": str(r.page)
            })
    # metadata minimal CLDF
    meta = {
        "dc:conformsTo": "http://cldf.clld.org/v1.0/terms.rdf#Generic",
        "tables": [
            {"url":"examples.csv", "dc:conformsTo":"http://cldf.clld.org/v1.0/terms.rdf#ExampleTable", "tableSchema":{"columns":[{"name":c} for c in EXAMPLE_COLUMNS]}},
            {"url":"languages.csv", "dc:conformsTo":"http://cldf.clld.org/v1.0/terms.rdf#LanguageTable", "tableSchema":{"columns":[{"name":c} for c in LANGUAGE_COLUMNS]}},
            {"url":"sources.csv", "dc:conformsTo":"http://cldf.clld.org/v1.0/terms.rdf#SourceTable", "tableSchema":{"columns":[{"name":c} for c in SOURCE_COLUMNS]}},
        ]
    }
    (outdir/"cldf-metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")


def write_report(pdf: Path, records: List[Record], meta: dict, stats: Counter, outdir: Path):
    kept=[r for r in records if not r.skipped]; skipped=[r for r in records if r.skipped]
    lang_counts=Counter(r.language or "Undetermined" for r in kept)
    reason_counts=Counter(r.reason for r in skipped)
    rows=[]
    rows.append(f"# Extraction report: {pdf.name}\n")
    rows.append(f"Article: {meta.get('citation','')}\n")
    rows.append(f"Candidates: {stats['candidate_blocks']}  ")
    rows.append(f"Kept: {len(kept)}  ")
    rows.append(f"Skipped: {len(skipped)}\n")
    rows.append("## Kept examples by language\n")
    for k,v in lang_counts.most_common(): rows.append(f"- {k}: {v}")
    rows.append("\n## Skip reasons\n")
    for k,v in reason_counts.most_common(): rows.append(f"- {k or 'unparsed'}: {v}")
    rows.append("\n## Kept example labels\n")
    rows.append(", ".join(f"({r.label})" for r in kept) or "None")
    rows.append("\n## Skipped examples\n")
    for r in skipped[:300]: rows.append(f"- ({r.label}) p.{r.page}: {r.reason}")
    (outdir/f"{pdf.stem}_report.md").write_text("\n".join(rows)+"\n", encoding="utf-8")


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("pdfs", nargs="+", type=Path)
    ap.add_argument("-o", "--outdir", type=Path, default=Path("cldf_examples"))
    args=ap.parse_args(argv)
    all_records=[]; metas={}; stats_all={}
    args.outdir.mkdir(parents=True, exist_ok=True)
    for pdf in args.pdfs:
        recs, meta, stats = parse_records(pdf)
        all_records.extend(recs); metas[pdf.stem]=meta; stats_all[pdf.name]=dict(stats)
        write_report(pdf, recs, meta, stats, args.outdir)
        print(f"{pdf.name}: kept {stats['kept']} / {stats['candidate_blocks']} candidates; skipped {stats['skipped']}", file=sys.stderr)
    write_outputs(all_records, metas, args.outdir)
    (args.outdir/"run_summary.json").write_text(json.dumps({"stats":stats_all, "records":[asdict(r) for r in all_records]}, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(f"Wrote CLDF dataset to {args.outdir}", file=sys.stderr)

if __name__ == "__main__": main()
