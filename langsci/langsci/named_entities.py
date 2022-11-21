import json
#import glob
import requests
import re
#import sys
from collections import defaultdict

try:
    from misextractions import misextractions
except ImportError:
    from langsci.misextractions import misextractions


NUMPATTERN = re.compile("[A-Za-z][-0-9]+")  # stuff like M2-34 is not any good

#offset = 0
#try:
    #offset = int(sys.argv[1])
#except IndexError:
    #pass


#nercache = json.loads(open("nercache.json").read())
entitiescache = json.loads(open("entitiestitles.json").read())
parentcache = defaultdict(dict)

with open("closure.csv") as closurefile:
    for line in closurefile.readlines():
        ancestor, degree, child = line.strip().split("\t")
        parentcache[child][ancestor] = True

def get_entities(text, cache=None):
    if cache:
        #global nercache
        try:
            entities = cache[text]
            return entities
        except KeyError:
            pass
    """send text to online resolver and retrieve wikidataId's"""
    ner_url = "https://cloud.science-miner.com/nerd/service/disambiguate"
    if len(text.split()) < 5:  # cannot do NER on less than 5 words
        return {}
    rtext = requests.post(ner_url, json={"text": text}).text
    # parse json
    print(rtext)
    if rtext == None or rtext == '':
        return {}
    retrieved_entities = json.loads(rtext).get("entities", [])
    # extract names and wikidataId's
    result = {
        x["wikidataId"]: x["rawName"]
        for x in retrieved_entities
        if x.get("wikidataId")
        and x["wikidataId"] not in misextractions
        and not NUMPATTERN.match(x["rawName"])
    }
    #if nercache:
        #nercache[text] = result
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
    for entity in entities:
        if entity in excludelist:
            continue
        parents += list(parentcache[entity].keys())
        result = {
            parent: get_title(parent)
            for parent in parents
            if parent not in entities and parent not in excludelist
        }
        return result


#for f in glob.glob("langscijson/*json")[offset:]:
    #print(f)
    #with open(f) as jsoncontent:
        #writedict = {}
        #file_examples = json.loads(jsoncontent.read())
        #for ex in file_examples:
            #ID = ex["ID"]
            #trs = ex["trs"]
            #try:
                #entities = nercache[trs]
            #except KeyError:
                #entities = get_entities(trs)
                #nercache[trs] = entities
            #writedict[ID] = {"entities": entities, "trs": trs}
    #entitiesfile = f.replace("langscijson", "entitiesjson")
    #with open(entitiesfile, "w") as entitiesjson:
        #entitiesjson.write(json.dumps(writedict, indent=4, sort_keys=True))
    #with open("nercache.json", "w") as nercachejson:
        #nercachejson.write(json.dumps(nercache, indent=4, sort_keys=True))
