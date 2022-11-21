import sys
import json
import requests
import numpy
import matplotlib.pyplot as plt

# let us first obtain the Paperhive document ID related to a LangSci book ID
lsID = sys.argv[1]
lsidrequest = requests.get(
    "https://paperhive.org/api/document-items/by-document/external?type=langsci&id="
    + lsID
)
lsidformated = json.loads(lsidrequest.text)
# save the ID.
paperhiveid = lsidformated["documentItems"][0]["id"]

#paperhiveid = "stscTQ_iDyaZ"
paperhiverequest = requests.get(
    "https://paperhive.org/api/discussions?documentItem=" + paperhiveid
)
paperhiveformated = json.loads(paperhiverequest.text)
# get the number of pages
pages = []  # create empty list for storage of pages
print(lsID,len(paperhiveformated["discussions"]))
for discussion in paperhiveformated["discussions"]:
    for page in discussion["target"]["selectors"]["pdfTextPositions"]:
        pages += [page["pageNumber"]]

# stop at last page with comment, leaving further pages w/o comments out of the plot
numpages = max(pages)

# and now for plotting
n, bins, patches = plt.hist(pages, numpages)
plt.ylabel("number of comments")
plt.xlabel("page number")
plt.savefig("%s.png" % lsID)
plt.show()
