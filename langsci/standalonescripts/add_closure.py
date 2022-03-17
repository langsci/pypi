from collections import defaultdict
import pprint
import glob
import json
import wptools


from philosophicalnonsense import nonsense

from misextractions import misextractions

entitiescache = json.loads(open("entitiestitles.json").read())

d = defaultdict(dict)


def get_title(wikidata_ID):
    global entitiescache
    try:
        title = entitiescache[wikidata_ID]
    except KeyError:
        try:
            title = wptools.page(wikibase=wikidata_ID,silent=True).get_wikidata().data.get('title', 'no title')
        except: #API KeyError
            title = None
        entitiescache[wikidata_ID] = title
    return title

with open("closure.csv")  as closurefile:
    for line in closurefile.readlines():
        ancestor, degree, child = line.strip().split("\t")
        d[child][ancestor] = True

for f in glob.glob("entitiesjson/*json"):
    outjson = None
    with open(f) as incontent:
        file_examples = json.loads(incontent.read())
    for ex in file_examples:
        entities = file_examples[ex]["entities"]
        parents = []
        for entity in entities:
            if entity in misextractions:
                continue
            parents += list(d[entity].keys())
        parents = {parent:get_title(parent) for parent in parents
                        if parent not in entities
                        and parent not in nonsense}
        if parents != {}:
            file_examples[ex]["parententities"] = parents
            print(30*'-')
            print(entities)
            pprint.pprint(parents)
    with open(f.replace("entitiesjson", "closurejson"), "w") as outcontent:
        outjson = json.dumps(file_examples, indent=4, sort_keys=True)
        outcontent.write(outjson)


with open("entitiestitles.json","w") as out:
    out.write(json.dumps(entitiescache, indent=4, sort_keys=True))

