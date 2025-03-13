import pprint
import sys
import csv
from lxml import etree
import glob
import hashlib
# filename =  "/home/snordhoff/versioning/git/langsci/pypi/langsci/wrapperscripts/inel/nar/AnIM_2009_Accident_nar/AnIM_2009_Accident_nar.exb"


licence = 'CC-BY-NC-SA'
ts_name = "Primary_Text"
mb_name = "Analyzed_Word"
ge_name = "Gloss"
fe_name = "Translated_Text"

languages  = {'dolgan':{'glottocode':'dolg1241',
                        'language_name':'Dolgan',
                        'source':"https://hdl.handle.net/11022/0000-0007-F9A7-4"
                        },
               'enets':{'glottocode':'enet1250',
                        'language_name':'Enets',
                        'source':"https://hdl.handle.net/11022/0000-0007-FE1D-C"
                        },
               'nenets':{'glottocode':'nene1251',
                        'language_name':'Nenets',
                        'source':"https://hdl.handle.net/11022/0000-0007-FE37-E"
                        },
               'evenki':{'glottocode':'even1259',
                        'language_name':'Evenki',
                        'source':"https://hdl.handle.net/11022/0000-0007-FE38-D"
                        },
               'kamas':{'glottocode':'kama1378',
                        'language_name':'Kamas',
                        'source':"http://hdl.handle.net/11022/0000-0007-FC25-4"
                        },
               'selkup':{'glottocode':'selk1253',
                        'language_name':'Selkup',
                        'source':"https://hdl.handle.net/11022/0000-0007-F4D9-1"
                        },
            }

def construct_id(el):
    start = int(el.attrib['start'][1:])
    end = int(el.attrib['end'][1:])
    id_ = (start,end)
    return id_

def processfile(f, lg):
    glottocode = languages[lg]['glottocode']
    language_name =  languages[lg]['language_name']
    source = languages[lg]['source']
    tree = etree.parse(f)
    root = tree.getroot()
    d_words = {}
    d_morphemes = {}

    ts_tier = root.find(".//tier[@id='ts']")
    mb_tier = root.find(".//tier[@id='mb']")
    ge_tier = root.find(".//tier[@id='ge']")
    fe_tier = root.find(".//tier[@id='fe']")

    try:
        for event in ts_tier.findall("./event"):
            id_ = construct_id(event)
            text = event.text
            d_words[id_] = {}
            d_words[id_][ts_name] = text.strip()
            d_words[id_][fe_name] = ''
    except AttributeError:
        print(f"No transcription for {filename}")
        return

    for event in mb_tier.findall("./event"):
        id_ = construct_id(event)
        text = event.text
        d_morphemes[id_] = {}
        d_morphemes[id_][mb_name] = text

    for event in ge_tier.findall("./event"):
        id_ = construct_id(event)
        text = event.text
        d_morphemes[id_][ge_name] = text
    try:
        for event in fe_tier.findall("./event"):
            id_ = construct_id(event)
            text = event.text
            d_words[id_][fe_name] = text.strip()
    except KeyError:
        print(f'Could not match translation for {filename}')


    for el in d_words:
        morphemes = []
        glosses = []
        start = el[0]
        end = el[1]
        current = start
        while current < end:
            try:
                next_item = d_morphemes[(current,current+1)]
                next_morpheme = next_item[mb_name]
                next_gloss = next_item[ge_name]
            except KeyError:
                next_morpheme = "_"
                next_gloss = "_"
            morphemes.append(next_morpheme)
            glosses.append(next_gloss)
            current += 1
        morpheme_string = " ".join(morphemes)
        gloss_string = " ".join(glosses)
        d_words[el][mb_name] = morpheme_string
        d_words[el][ge_name] = gloss_string
    basename = filename.split('/')[-1]
    barename = basename[:-4]
    number = str(int(hashlib.sha256(barename.encode("utf-8")).hexdigest(),16))[:10]
    doc_id = 'inel' + language + number
    for item in d_words:
        d_words[item]['ID'] = f"{doc_id}_{item[0]}_{item[1]}"
        d_words[item]['Language_ID'] = glottocode
        d_words[item]['Meta_Language_ID'] = 'stan1293'
        d_words[item]['LGRConformance'] = ''
        d_words[item]['Comment'] = ''
        d_words[item]['LGR_Conformance_Level'] = 2
        d_words[item]['Language_Name'] = language_name
        d_words[item]['Abbreviations'] = ''
        d_words[item]['Corpus_Reference'] = ''
        d_words[item]['Source'] = source
        d_words[item]['Contribution_ID'] = doc_id
        d_words[item]['Licence'] = licence
        d_words[item]['Abbreviations'] = {}


    with open(f'csv/{doc_id}.csv', 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)
        csv_writer.writerow(
            "ID Primary_Text Analyzed_Word Gloss Translated_Text Comment LGRConformance Contribution_ID Source Language_ID Meta_Language_ID Abbreviations".split()
        )
        for item in d_words:
            csv_writer.writerow([d_words[item]['ID'],
                                d_words[item]['Primary_Text'],
                                d_words[item]['Analyzed_Word'],
                                d_words[item]['Gloss'],
                                d_words[item]['Translated_Text'],
                                d_words[item]['Comment'],
                                d_words[item]['LGRConformance'],
                                d_words[item]['Contribution_ID'],
                                d_words[item]['Source'],
                                d_words[item]['Language_ID'],
                                d_words[item]['Meta_Language_ID'],
                                d_words[item]['Abbreviations']
                                ]
                                )

# pprint.pprint(d_words)


for language in languages:
    print(language)
    for filename in glob.glob(f'{language}/*/*/*exb'):
        processfile(filename, language)


