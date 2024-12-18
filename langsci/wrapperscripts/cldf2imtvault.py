import json
import sys
import csv
from os.path import exists

try:
    import titlemapping
    from interlinear import gll
except ImportError:
    from langsci import titlemapping
    from langsci.interlinear import gll

import re

CLLD_D = {"1":"wals",
        "2":"apics",
        "3":"autotyp",
        "4":"grambank",
        "5":"dplace",
        "6":"pulotu",
        "7":"acd",
        "8":"uratyp",
        "9":"elcat",
        "10":"igasttdir",
        "11":"jacquesestimative",
        "12":"malchukovditransitives",
        "13":"dictionariadaakaka",
        "14":"dictionariakalamang",
        "15":"dictionarianen",
        "16":"dictionariapalula",
        "17":"dictionariasidaama"
}

PROVIDER_ID_PATTERN = re.compile("([a-z]+)([0-9]+)")
skipexisting = True
nercache = json.loads(open("nercache.json").read())
filenametemplate = "langscijson/cldfexamples%s.json"
examples = []
current_docID = "dummy"
skipped_ID = ""
try:
    infile = sys.argv[1]
except IndexError:
    infile = "examples.csv"
with open(infile, newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    for count, row in enumerate(reader):
        # print(row['ID'])
        raw_ID = row["Contribution_ID"]
        m = PROVIDER_ID_PATTERN.match(raw_ID)
        provider = m.group(1)
        provider_ID = m.group(2)
        doc_ID = raw_ID
        if skipexisting and exists(filenametemplate % doc_ID):
            if doc_ID != skipped_ID:
                print(f"skipping {doc_ID}, already present")
                skipped_ID = doc_ID
            continue
        citation = row["Source"]
        external_ID = row["ID"]
        # print(external_ID)
        if provider == 'cldf':
            provider = CLLD_D[provider_ID]
            provider_ID = '0'
        thisgll = gll(
            "",
            row["Language_ID"],
            row["Analyzed_Word"],
            row["Gloss"],
            row["Translated_Text"],
            book_metalanguage=row["Meta_Language_ID"],
            abbrkey=json.loads(row["Abbreviations"]),
            filename=provider_ID + "/",
            provider=provider,
            categories="allcaps",
            analyze=True,
            extract_entities=True,
            extract_parent_entities=True,
            provided_citation=citation,
            external_ID=external_ID,
            nercache=nercache,
        )
        if doc_ID != current_docID:
            print(f"writing out {current_docID}")
            exlist = [ex.__dict__ for ex in examples]
            thisjson = json.dumps(
                exlist,
                sort_keys=True,
                indent=4,
                ensure_ascii=False,
            )
            jsonname = f"langscijson/cldfexamples{current_docID}.json"
            with open(jsonname, "w", encoding="utf8") as jsonout:
                jsonout.write(thisjson)
            # with open("nercache.json", "w") as nerout:
            # nerout.write = json.dumps(nercache,
            # sort_keys=True,
            # indent=4,
            # ensure_ascii=False)
            examples = []
            current_docID = doc_ID
            print(f"reading examples for {current_docID}")
        examples.append(thisgll)
    print(f"writing out {current_docID}")
    exlist = [ex.__dict__ for ex in examples]
    thisjson = json.dumps(
        exlist,
        sort_keys=True,
        indent=4,
        ensure_ascii=False,
    )
    jsonname = f"langscijson/cldfexamples{current_docID}.json"
    with open(jsonname, "w", encoding="utf8") as jsonout:
        jsonout.write(thisjson)
        # try:
        # nercache[thisgll.trs] = thisgll.entities
        # except AttributeError:
        # pass

# with open("nercache.json", "w") as nercachejson:
#     nercachejson.write(json.dumps(nercache, indent=4, sort_keys=True))
