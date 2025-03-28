from interlinear import gll

import glob
import sys

# import re
# import sre_constants
# import pprint
import json

# import operator
# import os
import LaTexAccents

# import requests
# import hashlib

# from bs4 import BeautifulSoup
from collections import defaultdict

# from titlemapping import titlemapping
# from lgrlist import LGRLIST

from imtvaultconstants import *
from langsci.webglottolog import string2glottocode, glottocode2iso

converter = LaTexAccents.AccentConverter()


def extract_examples(
    s, filename, book_language=None, book_metalanguage="eng", abbrkey={}
):
    s = s.replace(r"{\bfseries ", r"\textbf{")
    s = s.replace(r"{\itshape ", r"\textit{")
    s = s.replace(r"{\scshape ", r"\textsc{")
    if abbrkey == {}:
        try:
            abbr1 = s.split("section*{Abbreviations}")[1]
            abbr2 = abbr1.split(r"\section")[0]
            abbrkey = get_abbreviations(abbr2.split("\n"))
        except IndexError:
            pass
    examples = []
    for g in [m.groupdict() for m in GLL.finditer(s)]:
        presource = g["presourceline"] or ""
        lg = g["language_name"]
        if g["imtline2"] in (None, ""):  # standard \gll example¨
            src = g["sourceline"]
            imt = g["imtline1"]
        else:
            # we ignore the first line of \glll examples as the second line typically contains the morpheme breaks
            src = g["imtline1"]
            imt = g["imtline2"]
        trs = g["translationline"]
        try:
            thisgll = gll(
                presource,
                lg,
                src,
                imt,
                trs,
                filename=filename,
                book_language=book_language,
                book_metalanguage=book_metalanguage,
                abbrkey=abbrkey,
                glottolog=True,
                analyze=False,
                extract_entities=True,
                parent_entities=True,
                provider=None,
                nercache={},
            )
            if thisgll.book_ID in NON_CCBY_LIST:
                continue
        except AssertionError:
            continue
        examples.append(thisgll)
    return examples


def get_abbreviations(lines):
    result = {}
    for line in lines:
        if line.strip().startswith("%"):
            continue
        cells = line.split("&")
        if len(cells) == 2:
            abbreviation = gll.resolve_lgr(None, gll.striptex(None, cells[0]).strip())
            if abbreviation == "...":
                continue
            expansion = (
                gll.striptex(None, cells[1])
                .replace(r"\\", "")
                .strip()
                .replace(r"\citep", "")
            )
            result[abbreviation] = expansion
    return result


def langsciextract(directory):
    books = glob.glob(f"{directory}/*")
    # books = glob.glob(f"{directory}/16")
    for book in books:
        book_ID = int(book.split("/")[-1])
        if book_ID in SUPERSEDED:
            continue
        book_metalanguage = "eng"
        if book_ID in PORTUGUESE:
            book_metalanguage = "por"
        if book_ID in GERMAN:
            book_metalanguage = "deu"
        if book_ID in FRENCH:
            book_metalanguage = "fra"
        if book_ID in SPANISH:
            book_metalanguage = "spa"
        if book_ID in CHINESE:
            book_metalanguage = "cmn"
        book_language = ONE_LANGUAGE_BOOKS.get(int(book_ID), False)
        glossesd = defaultdict(int)
        excludechars = ".\\}{=~:/"
        abbrkey = {}
        try:
            with open(f"{directory}/{book_ID}/abbreviations.tex") as abbrin:
                abbrkey = get_abbreviations(abbrin.readlines())
        except FileNotFoundError:
            pass
        files = glob.glob(f"{directory}/{book_ID}/chapters/*tex")
        files = glob.glob(f"{directory}/{book_ID}/*tex")
        # print(" found %i tex files for %s" % (len(files), book_ID))
        for filename in files:
            try:
                s = open(filename).read()
            except UnicodeDecodeError:
                print("Unicode problem in %s" % filename)
            examples = extract_examples(
                s,
                filename,
                book_language=book_language,
                book_metalanguage=book_metalanguage,
            )
            if examples != []:
                jsons = json.dumps(
                    [ex.__dict__ for ex in examples],
                    sort_keys=True,
                    indent=4,
                    ensure_ascii=False,
                )
                jsonname = "langscijson/%sexamples.json" % filename[:-4].replace(
                    "/", "-"
                )
                print("   ", jsonname)
                with open(jsonname, "w", encoding="utf8") as jsonout:
                    jsonout.write(jsons)

    # with open("glottonames.json", "w") as namesout:
    # namesout.write(
    # json.dumps(glottonames, sort_keys=True, indent=4, ensure_ascii=False)
    # )
    # with open("glottoiso.json", "w") as glottoisoout:
    # glottoisoout.write(
    # json.dumps(glotto_iso6393, sort_keys=True, indent=4, ensure_ascii=False)
    # )


if __name__ == "__main__":
    langsciextract(sys.argv[1])
