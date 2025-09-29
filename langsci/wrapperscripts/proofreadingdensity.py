import sys
import json
import requests
import numpy
import matplotlib.pyplot as plt

# let us first obtain the Paperhive document ID related to a LangSci book ID
input_ = sys.argv[1]

try:
    int(input_)
    lsidrequest = requests.get(
        "https://paperhive.org/api/document-items/by-document/external?type=langsci&id="
        + input_
    )
    lsidformated = json.loads(lsidrequest.text)
    # save the ID.
    paperhiveid = lsidformated["documentItems"][0]["id"]
except ValueError:
    print("Input is not a LangSci ID. Assuming input is a PaperHive ID")
    paperhiveid = input_

# paperhiveid = "stscTQ_iDyaZ"
paperhiverequest = requests.get(
    "https://paperhive.org/api/discussions?documentItem=" + paperhiveid
)
paperhiveformated = json.loads(paperhiverequest.text)
# get the number of pages
pages = []  # create empty list for storage of pages
print(input_, len(paperhiveformated["discussions"]))
for discussion in paperhiveformated["discussions"]:
    for page in discussion["target"]["selectors"]["pdfTextPositions"]:
        pages += [page["pageNumber"]]

# stop at last page with comment, leaving further pages w/o comments out of the plot
numpages = max(pages)

# and now for plotting
n, bins, patches = plt.hist(pages, numpages)
plt.ylabel("number of comments")
plt.xlabel("page number")
plt.savefig("%s.png" % input_)
plt.show()
