import json
import sys
import csv
from os.path import exists
import requests

from langsci import titlemapping, langscipressorg_webcrawler
from langsci.interlinear import gll
from langsci.webglottolog import glottocode2countries, glottocode2geocoords
from langsci.macroareas import macroarea_d

import re

# def glossa_id2creator(id_):
#     url = f"https://www.glossa-journal.org/article/id/{id_}"
#     html = requests.get(url).text
#     soup = BeautifulSoup(html, "html.parser")
#     head = soup.find('head')
#     authorstring = ' & '.join([x.attrs['content'] for x in head.select("meta[name='citation_author']")])
#     return authorstring


citation_d = {}
with open('contributions.csv', newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        id_ = row['ID']
        citation_d[id_] = row['Citation']
citation_d['ineldolgan'] = "Däbritz, Chris Lasse; Kudryakova, Nina; Stapert, Eugénie. 2022. INEL Dolgan Corpus. Version 2.0. Publication date 2022-11-30. https://hdl.handle.net/11022/0000-0007-F9A7-4."
citation_d['inelkamas'] = "Gusev, Valentin; Klooster, Tiina; Wagner-Nagy, Beáta. 2023. “INEL Kamas Corpus.” Version 2.0. Publication date 2023-12-31. http://hdl.handle.net/11022/0000-0007-FC25-4"
citation_d['inelselkup'] = "Brykina, Maria; Orlova, Svetlana; Wagner-Nagy, Beáta. 2021. “INEL Selkup Corpus.” Version 2 .0. Publication date 2021-12-31. https://hdl.handle.net/11022/0000-0007-F4D9-1"
citation_d['inelevenki'] = "Däbritz, Chris Lasse; Gusev, Valentin; Stoynova, Natalia. 2024. INEL Evenki Corpus. Version 2.0. Publication date 2024-12-31. Archived at Universität Hamburg. https://hdl.handle.net/11022/0000-0007-FE38-D"
citation_d['inelenets'] = "Shluinsky, Andrey; Khanina, Olesya; Wagner-Nagy, Beáta. 2024. INEL Enets Corpus. Version 1.0. Publication date 2024-11-30. https://hdl.handle.net/11022/0000-0007-FE1D-C"
citation_d['inelnenets'] = "Budzisch, Josefina; Wagner-Nagy, Beáta. 2024. INEL Nenets Corpus. Version 1.0. Publication date 2024-12-31. https://hdl.handle.net/11022/0000-0007-FE37-E."



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

PROVIDER_ID_PATTERN = re.compile("([a-z]+)([0-9,]+)")
skipexisting = True
nercache = json.loads(open("nercache.json").read())
countrycache = json.loads(open("countrycache.json").read())
coordscache = json.loads(open("coordscache.json").read())
ancestors = json.loads(open("ancestors.json").read())
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
        thisgll.entities += thisgll.parententities
        try:
            thisgll.countries = countrycache[thisgll.language_glottocode]
        except AttributeError:
            print(f'no glottocode')
        except KeyError:
            print(f'no country for {thisgll.language_glottocode} in cache')
            thisgll.countries = glottocode2countries(thisgll.language_glottocode)
            print(f' found {thisgll.countries}')
            countrycache[thisgll.language_glottocode] = thisgll.countries
        try:
            thisgll.macroareas = list({macroarea_d[country["ISO3166"]] for country in thisgll.countries})
        except AttributeError:
            thisgll.macroareas = []
        try:
            thisgll.coords = coordscache[thisgll.language_glottocode]
        except AttributeError:
            print(f'no glottocode')
        except KeyError:
            print(f'no coords for {thisgll.language_glottocode} in cache')
            thisgll.coords = glottocode2geocoords(thisgll.language_glottocode)
            print(f' found {thisgll.coords}')
            coordscache[thisgll.language_glottocode] = thisgll.coords
        try:
            thisgll.ancestors = [{'label': a[1], 'id':a[0]} for a  in ancestors[thisgll.language_glottocode]]
        except AttributeError:
            thisgll.ancestors = []
        except KeyError:
            print(f"{thisgll.language_glottocode} is a glottocode which does not have proper ancestors")
            thisgll.ancestors = []
            ancestors[thisgll.language_glottocode] = []
        # thisgll.licence = "CC-BY"
        if thisgll.provider.startswith("inel"):
            thisgll.licence = "https://creativecommons.org/licenses/by-nc-sa/4.0/"
        thisgll.rightsholder = "unknown"
        citation_ID = raw_ID
        for s in "dolgan enets nenets evenki kamas selkup".split():
            if citation_ID.startswith(f"inel{s}"):
                citation_ID = f"inel{s}"
        try:
            thisgll.rightsholder = citation_d[citation_ID]
        except KeyError:
            print(f'rightsholder could not be established for {raw_ID}')
            citation_d[citation_ID] = 'unknown'
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
with open("countrycache.json", "w") as countrycachejson:
    countrycachejson.write(json.dumps(countrycache, indent=4, sort_keys=True))
with open("coordscache.json", "w") as coordscachejson:
    coordscachejson.write(json.dumps(coordscache, indent=4, sort_keys=True))
