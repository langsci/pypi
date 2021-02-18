import json
import requests

documents = {}
#for i in range(16,310):
for i in[286,268,282177,287, 283,252,278,275,276,263,230,270,261,253,148,228,213,256,254,239,250,194,260,235,258,271,274,265,178,297]:
    print(i, end=" ")
    masterurl = "https://paperhive.org/api/document-items/by-document/external?type=langsci&id=%s"%i
    #print(masterurl)
    masterjson = json.loads(requests.get(masterurl).text)
    try:
        proofreadingversion_ID = masterjson["documentItems"][0]["id"]
    except KeyError: #no discussions or no document
        print("not a valid ID")
        continue
    discussions_url = "https://paperhive.org/api/discussions?documentItem=%s" % proofreadingversion_ID
    #print(discussions_url)
    discussionsjson = json.loads(requests.get(discussions_url).text)
    discussions = discussionsjson["discussions"]
    print(len(discussions))
    documents[i] = len(discussions)

with open("paperhive.json", "w") as out:
    out.write(json.dumps(documents))





