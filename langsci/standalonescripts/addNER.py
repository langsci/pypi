import json
import glob
import requests
import re

ROADPATTERN = re.compile("R[0-9]+")


NER_BLACKLIST = [
    "Q4917", #'$', used for Latex escapes
    "Q7946755", #'wasn', radio station
    "Q3089073", #'happy, happy', norwegian comedy film
    "Q19893364",#'Inside The Tree', music album
    "Q49084,"# ss/ short story
    "Q17646620",# "don't" Ed Sheeran song
    "Q2261572",# "he/she" Gender Bender
    "Q35852",# : "ha" hectare
    "Q119018",#: "Mhm" Mill Hill Missionaries
    "Q932347",# "gave",# generic name referring to torrential rivers, in the west side of the Pyrenees
    "Q16836659", #"held" feudal land tenure in England
    "Q914307",# "ll" Digraph
    "Q3505473",# "stayed" Stay of proceedings
    "Q303",# "him/her" Elvis Presley
    "Q2827398",#: "Aha!" 2007 film by Enamul Karim Nirjhar
    "Q1477068",# "night and day" Cole Porter song
    "Q1124888",# "CEDA" Spanish Confederation of the Autonomous Right
    "Q1189745", # 'S/he'}

    ]

def get_entities(text):
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
            and x["wikidataId"] not in NER_BLACKLIST
            and not ROADPATTERN.match(x["rawName"])
            }

for f in glob.glob("langscijson/*json"):
    with open(f) as jsoncontent:
        writedict = {}
        file_examples = json.loads(jsoncontent.read())
        for ex in file_examples:
            ID = ex["ID"]
            trs = ex["trs"]
            entities = get_entities(trs)
            #if entities != {}:
                #print(trs)
                #print(f" {entities}")
            writedict[ID] = {"entities": entities, "trs": trs}
    entitiesfile = f.replace("langscijson", "entitiesjson")
    with open(entitiesfile, "w") as entitiesjson:
        print(writedict)
        entitiesjson.write(json.dumps(writedict, indent=4, sort_keys=True))



