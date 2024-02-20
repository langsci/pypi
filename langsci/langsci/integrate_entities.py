import json
import glob
import pprint

basefiles = glob.glob("langscijson/*json")

ld = False

context = {}
if ld:
    context = {
        "nextWord": "https://purl.org/liodi/ligt#nextWord",
        "hasWords": "https://purl.org/liodi/ligt#hasWords",
        "WordTier": "https://purl.org/liodi/ligt#WordTier",
        "item": "https://purl.org/liodi/ligt#item",
        "Word": "https://purl.org/liodi/ligt#Word",
        "topic": {"@id": "http://purl.org/dc/elements/1.1/subject", "@type": "@id"},
        "language": {"@id": "http://purl.org/dc/elements/1.1/language", "@type": "@id"},
        "label": "http://www.w3.org/2000/01/rdf-schema#label",
        "book_URL": "http://purl.org/dc/terms/isPartOf",
        "ID": "http://purl.org/dc/terms/identifier",
        "category": "http://purl.org/dc/terms/hasPart",
    }


def process_entities(d):
    l = [{"wdid": key, "label": d[key]} for key in d]
    return l


def ld_words(srcwords, imtwords, ex_ID, lg, imtlg):
    result = []
    assert len(srcwords) == len(imtwords)
    length = len(srcwords)
    for i, w in enumerate(srcwords):
        d = {
            "@type": "Word",
            "@label": [
                {"@value": srcwords[i], "@language": lg},
                {"@value": imtwords[i], "@language": imtlg},
            ],
            "@id": "_:%s_%i" % (ID, i),
            "nextWord": None if i == length - 1 else "_:%s_%i" % (ID, i + 1),
        }
        result.append(d)
    return result


for filename in basefiles:
    closurefilename = filename.replace("langscijson", "closurejson")
    outfilename = filename.replace("langscijson", "fulljson")
    with open(filename) as base:
        based = json.loads(base.read())
    try:
        with open(closurefilename) as closure:
            closured = json.loads(closure.read())
    except FileNotFoundError:
        print(f"{closurefilename} not found")
        continue
    outd = {}
    for ex in based:
        imtlg = "en-x-lgr"
        if ex["book_metalanguage"] == "fra":
            imtlg = "fr-x-lgr"
        if ex["book_metalanguage"] == "spa":
            imtlg = "es-x-lgr"
        if ex["book_metalanguage"] == "por":
            imtlg = "pt-x-lgr"
        if ex["book_metalanguage"] == "deu":
            imtlg = "de-x-lgr"
        if ex["book_metalanguage"] == "cmn":
            imtlg = "zh-x-lgr"
        ID = ex["ID"]
        # print(filename, closurefilename, ID)
        try:
            ex["entities"] = process_entities(closured[ID]["entities"])
            ex["parententities"] = process_entities(
                closured[ID].get("parententities", {})
            )
        except KeyError:
            print(f"Example {ID} not found in {closurefilename}")
            continue
        ex["book_URL"] = f"https://langsci-press.org/catalog/book/{ex['book_ID']}"
        ex["language"] = None
        if ex.get("language_glottocode", "und") != "und":
            ex[
                "language"
            ] = f"https://glottolog.org/resource/languoid/id/{ex['language_glottocode']}"
        srcstring = " ".join(ex["srcwordsbare"])
        imtstring = " ".join(ex["imtwordsbare"])
        ex["label"] = srcstring
        if ld:
            ex["@id"] = ID + "_u"
            ex["topic"] = [
                f"https://www.wikidata.org/wiki/{e['wdid']}"
                for e in ex["entities"] + ex["parententities"]
            ]
            ex["@type"] = "https://purl.org/liodi/ligt#utterance"
            ex["@context"] = context
            ex["hasWords"] = {
                "@type": "WordTier",
                "@id": ID + "_wt",
                "@label": [
                    {"@value": srcstring, "@language": ex["language"]},
                    {"@value": imtstring, "@language": imtlg},
                ],
                "item": ld_words(
                    ex["srcwordsbare"],
                    ex["imtwordsbare"],
                    ex["ID"],
                    ex["language_glottocode"],
                    imtlg,
                ),
            }
        outd[ex["ID"]] = ex
    with open(outfilename, "w") as out:
        out.write(
            json.dumps(
                [outd[k] for k in outd], indent=4, sort_keys=True, ensure_ascii=False
            )
        )
