import json
import csv
from interlinear import gll
import re

PROVIDER_ID_PATTERN = re.compile("([a-z]+)([0-9]+)")

nercache = json.loads(open("nercache.json").read())

examples = []
with open('examples.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        print(row['ID'])
        raw_ID = row['Contribution_ID']
        m = PROVIDER_ID_PATTERN.match(raw_ID)
        provider = m.group(1)
        provider_ID = m.group(2)
        citation = row['Source']
        external_ID = row['ID']
        thisgll = gll(
            '',
            row['Language_ID'],
            row['Analyzed_Word'],
            row['Gloss'],
            row['Translated_Text'],
            book_metalanguage = row['Meta_Language_ID'],
            abbrkey = json.loads(row['Abbreviations']),
            filename = provider_ID + "/",
            provider = provider,
            categories = "allcaps",
            analyze = True,
            extract_entities = True,
            parent_entities = True,
            provided_citation = citation,
            external_ID = external_ID
            )
        examples.append(thisgll)

if examples != []:
        jsons = json.dumps(
            [ex.__dict__ for ex in examples],
            sort_keys=True,
            indent=4,
            ensure_ascii=False,
        )
        jsonname = "langscijson/cldfexamples.json"
        with open(jsonname, "w", encoding="utf8") as jsonout:
            jsonout.write(jsons)

