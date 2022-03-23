import json
import glob
import requests
import re
import sys

from misextractions import  misextractions

NUMPATTERN = re.compile("[A-Za-z][-0-9]+") #stuff like M2-34 is not any good

offset = 0
try:
    offset = int(sys.argv[1])
except IndexError:
    pass

nercache = json.loads(open("nercache.json").read())

def get_entities(text):
    global nercache
    """sent text to online resolver and retrieve wikidataId's"""
    ner_url = "https://cloud.science-miner.com/nerd/service/disambiguate"
    if len(text.split()) < 5:  # cannot do NER on less than 5 words
        return {}
    rtext = requests.post(ner_url, json={"text": text}).text
    # parse json
    if rtext == None:
        return {}
    retrieved_entities = json.loads(rtext).get("entities", [])
    # extract names and wikidataId's
    return {x["wikidataId"]: x["rawName"]
            for x in retrieved_entities
            if x.get("wikidataId")
            and x["wikidataId"] not in misextractions
            and not NUMPATTERN.match(x["rawName"])
            }

for f in glob.glob("langscijson/*json")[offset:]:
    print(f)
    with open(f) as jsoncontent:
        writedict = {}
        file_examples = json.loads(jsoncontent.read())
        for ex in file_examples:
            ID = ex["ID"]
            trs = ex["trs"]
            try:
                entities = nercache[trs]
            except KeyError:
                entities = get_entities(trs)
                nercache[trs] = entities
            writedict[ID] = {"entities": entities, "trs": trs}
    entitiesfile = f.replace("langscijson", "entitiesjson")
    with open(entitiesfile, "w") as entitiesjson:
        entitiesjson.write(json.dumps(writedict, indent=4, sort_keys=True))
    with open("nercache.json", "w") as nercachejson:
        nercachejson.write(json.dumps(nercache, indent=4, sort_keys=True))







