from collections import defaultdict
import pprint
import glob
import json


from philosophicalnonsense import nonsense

d = defaultdict(dict)

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
            parents += list(d[entity].keys())
        parents = list({parent for parent in parents if parent not in entities and parent not in nonsense})
        if parents != []:
            file_examples[ex]["parententities"] = parents
    entitiesfile = f.replace("langscijson", "entitiesjson")
    with open(f.replace("entitiesjson", "closurejson"), "w") as outcontent:
        outjson = json.dumps(file_examples, indent=4, sort_keys=True)
        print(outjson)
        outcontent.write(outjson)
