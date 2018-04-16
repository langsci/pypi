import requests
import json
import pprint 
import yaml


localdata = yaml.load(open('test.yaml','r')) 
chapter = False

print(localdata)
tokenfile = open('zenodo.token')
token = open('zenodo.token').read().strip()
tokenfile.close()

print(token)

metadata={'upload_type': 'publication',
        'access_right':'open',
        'license':'cc-by',
        'imprint_publisher':'Language Science Press',
        'imprint_place':'Berlin',
        'communities': [{'identifier':'Language Science Press'}],
        'prereserve_doi': True, 
        'language':'eng',
        'publication_type':'book'
    }

#if chapter:
    #metadata['publication_type'] = 'section'
    #metadata['imprint_isbn'] = localdata.isbn 
    #metadata['partof_title'] = chapter.booktitle
    #metadata['partof_pages'] = chapter.pagerange
    #metadata['related_identifiers'] = [{'hasPart':chapter.booktitle}] #unintuitive directionality of hasPart and isPart
#else:
    #metadata['related_identifiers'] = [{'isAlternateIdentifier':localdata['isbn']}]
        
metadata['title']=localdata['title']
metadata['description']=localdata['description']
metadata['creators']=[{'name':localdata['author']}]  
try:
    metadata['keywords']= localdata['keywords'].split(',')        
except KeyError:
    pass
#'subjects':[{'identifier':'http://glottolog.org/resource/languoid/id/stan1293'}],
#'creators': [{'name': 'Doe, John',
            #'affiliation': 'Zenodo'}],
#'keywords': ['',''],

data={
    #'filename': "test.csv",
    'metadata': metadata
}

pprint.pprint(json.dumps(data))        
        
r = requests.post('https://zenodo.org/api/deposit/depositions', 
                  params={'access_token': token}, 
                  json={},
                  headers = {"Content-Type": "application/json"},
                  data=json.dumps(data)
                  )

pprint.pprint(r.json())