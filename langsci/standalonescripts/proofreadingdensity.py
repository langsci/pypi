import sys
import json
import requests
import numpy
import matplotlib.pyplot as plt

# let us first obtain the Paperhive document ID related to a LangSci book ID
lsidrequest = requests.get('https://paperhive.org/api/document-items/by-document/external?type=langsci&id=' + sys.argv[1])
lsidformated = json.loads(lsidrequest.text)
# save the ID.
paperhiveid = lsidformated['documentItems'][0]['id']
paperhiverequest = requests.get('https://paperhive.org/api/discussions?documentItem=' + paperhiveid)
paperhiveformated = json.loads(paperhiverequest.text)
# get the number of pages
pages = [] # create empty list for storage of pages
for discussion in paperhiveformated['discussions']:  
    for page in discussion['target']['selectors']['pdfTextPositions']: 
        pages += [page['pageNumber']] 

numpages = max(pages) #stop at last page with comment, leaving further pages w/o comments out of the plot

# and now for plotting
n, bins, patches = plt.hist(pages,numpages)
plt.ylabel('number of comments')
plt.xlabel('page number')
plt.show()
