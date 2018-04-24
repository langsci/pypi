import requests
import json
import pprint 
import yaml
import glob
import re

INCLUDEPAPERP = re.compile("\\includepaper\{chapters/(.*?)\}")
BOOKAUTHORP = re.compile(r"\\author{(.*?)}")
LASTAND = re.compile(r"(\\lastand|\\and)")
CHAPTERAUTHORP = re.compile(r"\\author{(.*?)\\affiliation{(.*)}}")
TITLEP = re.compile(r"\\title{(.*?)}")
ISBNP = re.compile(r"\\lsISBNdigital}{(.*)}") 
CHAPTERKEYWORDSP = re.compile(r"\\keywords{(.*?)}")
ABSTRACTP = re.compile(r"\\abstract{(.*?)[}\n]")
BACKBODYP = re.compile(r"\\BackBody{(.*?)[}\n]")

class Publication():
  def __init__(self):
    self.metadata={'upload_type': 'publication',
            'access_right':'open',
            'license':'cc-by',
            'imprint_publisher':'Language Science Press',
            'imprint_place':'Berlin',
            'communities': [{'identifier':'Language Science Press'}],
            'prereserve_doi': True, 
            'language':'eng' 
        } 
    
class Book(Publication): 
  def __init__(self):
    Publication.__init__(self)
    self.title=None
    self.authors=[]
    self.abstract=None
    self.keywords=None
    self.digitalisbn=None
    self.getBookMetadata()
    self.chapter = []
    self.getChapters()
    self.metadata['publication_type'] = 'book'
    self.metadata['related_identifiers'] = [{'isAlternateIdentifier':self.digitalisbn}]
    
  def getBookMetadata(self):
    localmetadataf = open('localmetadata.tex')
    localmetadata = localmetadataf.read()
    localmetadataf.close()
    self.title = TITLEP.search(localmetadata).group(1)
    authorstring = BOOKAUTHORP.search(localmetadata).group(1)
    authors = []
    for i, au in enumerate(LASTAND.split(authorstring)):
        if i%2 == 0:#get rid of splitters, i.e. "and" and "lastand" at odd positions
          authors.append(au.strip())
    self.authors = authors
    self.abstract = BACKBODYP.search(localmetadata).group(1)
    self.keywords = [x.strip() for x in CHAPTERKEYWORDSP.search(localmetadata).group(1).split(',')]
    self.digitalisbn = ISBNP.search(localmetadata).group(1) 
    
  def getChapters(self):
    mainf = open('main.tex')
    main = mainf.read()
    mainf.close()
    chapterpaths = INCLUDEPAPERP.findall(main) 
    self.chapters = [Chapter(cp,booktitle=self.title,isbn=self.digitalisbn) for cp in chapterpaths]
    

class Chapter(Publication):  
  def __init__ (self,path,booktitle='',isbn=False):
    Publication.__init__(self)
    chapterf = open('chapters/%s.tex'%path)
    chapter = chapterf.read()
    chapterf.close()
    preamble = chapter.split('\\begin{document}')[0]
    author, affiliation = CHAPTERAUTHORP.search(preamble).groups()
    title = TITLEP.search(preamble).group(1)
    abstract = ABSTRACTP.search(preamble).group(1)
    keywords = [x.strip() for x in CHAPTERKEYWORDSP.search(preamble).group(1).split(',')]    
    self.author = author
    self.title = title
    self.booktitle = booktitle
    self.abstract = abstract 
    self.keywords = keywords
    if isbn:
      self.bookisbn = isbn    
    self.metadata['publication_type'] = 'section'   
    self.metadata['imprint_isbn'] = self.bookisbn
    self.metadata['partof_title'] = self.booktitle
    #self.metadata['partof_pages'] = chapter.pagerange
    self.metadata['related_identifiers'] = [{'hasPart':self.bookisbn}] #unintuitive directionality of hasPart and isPart

if __name__ == "__main__":
  book = Book() 
  pprint.pprint(book.__dict__)
  for c in book.chapters:
    pprint.pprint(c.__dict__)
  0/0
  #tokenfile = open('zenodo.token')
  #token = open('zenodo.token').read().strip()
  #tokenfile.close()
  #print(token)


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