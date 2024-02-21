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
paperhiverequest = requests.get(
    "https://paperhive.org/api/discussions?documentItem=" + paperhiveid
)
paperhiveformated = json.loads(paperhiverequest.text)
# get the number of pages
pages = []  # create empty list for storage of pages
out = open("%s.tsv" % lsID, "w", encoding="utf8")
for i, discussion in enumerate(paperhiveformated["discussions"]):
    bookID = lsID
    commentID = i
    try:
        proofreaderID = discussion["author"]["id"]
    except KeyError:
        proofreaderID = "anonymous"
    pdftextpos = discussion["target"]["selectors"]["pdfTextPositions"][0]
    startpos = pdftextpos["start"]
    endpos = pdftextpos["end"]
    pagenumber = pdftextpos["pageNumber"]
    title = discussion["title"]
    body = discussion.get("body", "")
    out.write(
        "\t".join(
            [
                str(bookID),
                str(commentID),
                str(proofreaderID),
                str(pagenumber),
                str(startpos),
                str(endpos),
                title.replace('"', "'"),
                '"%s"' % body.replace('"', "'").replace("\n", " "),
            ]
        )
    )
    out.write("\n")
    for page in discussion["target"]["selectors"]["pdfTextPositions"]:
        pages += [page["pageNumber"]]
    numpages = max(pages)
out.close()
discussioncount = len(paperhiveformated["discussions"])
ratio = discussioncount / numpages
print("%s  %i  %i %s" % (bookID, numpages, discussioncount, ratio))
