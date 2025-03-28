import json

# import glob
import requests
import re

# import sys
from collections import defaultdict

from langsci.imtvault.misextractions import misextractions


NUMPATTERN = re.compile("[A-Za-z][-0-9]+")  # stuff like M2-34 is not any good

# offset = 0
# try:
# offset = int(sys.argv[1])
# except IndexError:
# pass


entitiescache = json.loads(open("entitiestitles.json").read())
parentcache = defaultdict(dict)

with open("closure.csv") as closurefile:
    for line in closurefile.readlines():
        ancestor, degree, child = line.strip().split("\t")
        parentcache[child][ancestor] = True


def get_entities(text, nercache=None):
    ner_url = "http://localhost:8090/service/disambiguate"
    URL     = "http://localhost:8090/service/disambiguate"
    try:
        cached_entities = nercache[text]
        try:
            return [x
                    for x in cached_entities
                    if x['wdid'] not in misextractions
                    ]
        except TypeError:
            list_ = [{'label':cached_entities[x][0], 'wdid': x}
                    for x in cached_entities
                    if x not in misextractions
                    ]
            nercache[text] = list_
            return list_
    except KeyError:
        pass
    except TypeError:
        print(f"TypeError for {text}")
    """send text to online resolver and retrieve wikidataId's"""
    # ner_url = "https://cloud.science-miner.com/nerd/service/disambiguate"
    if len(text.split()) < 5:  # cannot do NER on less than 5 words
        return []
    # rtext = requests.post(ner_url, json={"text": text}).text
    rtext = requests.post(URL, json={"text": text}, timeout=1200).text
    # parse json
    if rtext == None or rtext == "":
        return []
    retrieved_entities = json.loads(rtext).get("entities", [])
    # extract names and wikidataId's
    result =[{
        "wdid": x["wikidataId"],
        "label": x["rawName"]
        }
        for x in retrieved_entities
        if x.get("wikidataId")
        and x["wikidataId"] not in misextractions
        and not NUMPATTERN.match(x["rawName"])
        and x["confidence_score"] > 0.4
    ]
    # if nercache:
    nercache[text] = result
    # if result:
    #     print([x[0] for x in result.values()])
    # with open("nercache.json", "w") as nercachejson:
    #     nercachejson.write(json.dumps(nercache, indent=4, sort_keys=True))
    return result




def get_title(wikidata_ID):
    global entitiescache
    try:
        title = entitiescache[wikidata_ID]
    except KeyError:
        try:
            title = (
                wptools.page(wikibase=wikidata_ID, silent=True)
                .get_wikidata()
                .data.get("title", "no title")
            )
        except:  # API KeyError
            title = None
        entitiescache[wikidata_ID] = title
    return title


def get_parent_entities(entities, excludelist=misextractions):
    parents = []
    for entity_d in entities:
        entity = entity_d["wdid"]
        if entity in excludelist:
            continue
        parents += list(parentcache[entity].keys())
    result = [{"wdid": parent,
               "label": get_title(parent)
               }
                for parent in parents
                if parent not in entities and parent not in excludelist
            ]
    # print(result)
    return result


# for f in glob.glob("langscijson/*json")[offset:]:
# print(f)
# with open(f) as jsoncontent:
# writedict = {}
# file_examples = json.loads(jsoncontent.read())
# for ex in file_examples:
# ID = ex["ID"]
# trs = ex["trs"]
# try:
# entities = nercache[trs]
# except KeyError:
# entities = get_entities(trs)
# nercache[trs] = entities
# writedict[ID] = {"entities": entities, "trs": trs}
# entitiesfile = f.replace("langscijson", "entitiesjson")
# with open(entitiesfile, "w") as entitiesjson:
# entitiesjson.write(json.dumps(writedict, indent=4, sort_keys=True))
# with open("nercache.json", "w") as nercachejson:
# nercachejson.write(json.dumps(nercache, indent=4, sort_keys=True))
