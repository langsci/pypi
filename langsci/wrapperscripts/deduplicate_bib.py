from collections import defaultdict
from langsci.bibtools import *
import pprint

keepfields = ["author","year","title","journal","volume","number","pages","editor","address","publisher","url","doi","typ","note","addendum","booktitle","edition","howpublished","month","series"]
yeardic = defaultdict(dict)

bibfilestring = open(sys.argv[1]).read()
list_ = bibfilestring.split('\n@')

for s in list_:
    s = s.replace("""
		  """," ")
    m = re.match(bibpatterns.TYPKEYFIELDS,s)
    try:
        typ = m.group(1).lower()
    except AttributeError:
        pass
    try:
        key = m.group(2)
        fields = dict((tp[0].strip().lower()\
            .replace('\n',' ')\
            .replace('\t',' '),
            tp[1].strip()\
            .replace('\n',' ')\
            .replace('\t',' ')
                ) for tp in [re.split('\s*=\s*',t,maxsplit=1)
            for t in re.split('(?<=\})\s*,\s*\n',
                m.group(3).strip()
                )
            ]
                )
    except AttributeError:
        #print(f"could not be parsed: {s}")
        continue

    fieldaliases = (("location", "address"), ("date", "year"), ("journaltitle", "journal"))
    for old, new in fieldaliases:
        if fields.get(old) and not fields.get(new):
            fields[new] = fields[old]
            del fields[old]
    if "crossref"  in fields.keys():
        continue
    try:
        year = fields["year"]
    except KeyError:
        continue
    try:
        year = fields["title"]
    except KeyError:
        continue
    try:
        year = re.search("(\d+)", fields["year"]).group(1)
    except AttributeError:
        pass #leave forthcoming etc
    try:
        creator = fields["author"]
    except KeyError:
        try:
            creator = fields["editor"]
        except KeyError:
            continue
    newfields = {}
    for k in fields.keys():
        if k in keepfields:
            newfields[k] = fields[k]
    fields = newfields
    newfields["key"] = key.strip()
    newfields["typ"] = typ.strip()
    try:
        yeardic[year][creator].append(fields)
    except KeyError:
        yeardic[year][creator] = [fields]

#pprint.pprint(yeardic)


for year in yeardic:
    for creator in yeardic[year]:
        for i, record1 in enumerate(yeardic[year][creator]):
            if record1.get("merged"):
                continue
            for j, record2 in enumerate(yeardic[year][creator]):
                if record2.get("merged"):
                    continue
                if j <= i:
                    continue
                striptitle1 = re.sub('[^a-z]+', '', record1["title"].lower())
                striptitle2 = re.sub('[^a-z]+', '', record2["title"].lower())
                keeptitle = record1["title"]
                mergeflag = False
                if striptitle1 == striptitle2: #the titles are identical, but might have extra {}
                    mergeflag = True
                    if len(record2["title"]) > len(record1["title"]): #we want to keep the title with more {}, assuming that they protect capitalization
                        keeptitle = record2["title"]
                elif striptitle2 in striptitle1: #title 2 is shorter than title 1. We keep title 1
                    mergeflag = True
                elif striptitle1 in striptitle2: #title 1 is shorter than title 2. We keep title 2
                    mergeflag = True
                    keeptitle = record2["title"]
                if mergeflag:
                    for field in record2:
                        if len(record2[field]) > len(record1.get("field", "")):
                           record1[field] = record2[field]
                    record1["title"] = keeptitle
                    yeardic[year][creator][i] = record1
                    record2["merged"] = True
                    yeardic[year][creator][j] = record2
                    #print("merged")
        if record1.get("merged"):
            continue

        print("@%s{%s, " % (record1["typ"],record1["key"]))
        print("\t", end="")
        print(",\n\t".join(sorted([field +"= " +record1[field] for field in record1 if field not in ("key", "typ")])).replace(",,",","))
        print("}\n")




