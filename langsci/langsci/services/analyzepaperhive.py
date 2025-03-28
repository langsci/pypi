import json
import requests
import statistics

documents = {}
for i in range(16, 350):
    # for i in[259,236,142,245,326,298,295,308,319,280,281,293,303,321,289,316,304,305,311,313,290,262,327,150,317,323,315,296,299,288]:
    print(i, end=" ")
    masterurl = (
        "https://paperhive.org/api/document-items/by-document/external?type=langsci&id=%s"
        % i
    )
    # print(masterurl)
    masterjson = json.loads(requests.get(masterurl).text)
    try:
        proofreadingversion_ID = masterjson["documentItems"][0]["id"]
    except KeyError:  # no discussions or no document
        print("not a valid ID")
        continue
    discussions_url = (
        "https://paperhive.org/api/discussions?documentItem=%s" % proofreadingversion_ID
    )
    # print(discussions_url)
    discussionsjson = json.loads(requests.get(discussions_url).text)
    discussions = discussionsjson["discussions"]
    thisdoccomments = len(discussions)
    documents[i] = thisdoccomments

nonzerodocs = [documents[key] for key in documents if documents[key] > 0]
print()
print(nonzerodocs)
# print(" ".join([str(i) for i in nonzerodocs]))
totaldocs = len(nonzerodocs)
totalcomments = sum(nonzerodocs)
mean = statistics.mean(nonzerodocs)
median = statistics.median(nonzerodocs)

print(totaldocs, totalcomments, mean, median)

with open("paperhive.json", "w") as out:
    out.write(json.dumps(documents, indent=4))
