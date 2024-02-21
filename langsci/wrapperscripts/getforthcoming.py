import requests
from bs4 import BeautifulSoup

url = "https://langsci-press.org/catalog"
html = requests.get(url).text
soup = BeautifulSoup(html, "html.parser")
books = soup.find_all("div", "obj_monograph_summary")
meta = [
    (
        book.find("a", "title").text.strip(),
        book.find("div", "author")
        .text.strip()
        .replace("(Volume Editor)", "(eds.)")
        .replace(" (Author)", ""),
    )
    for book in books
]
for m in meta:
    if m[0].startswith("Forth"):
        title = m[0].replace("Forthcoming: ", "")
        creators = m[1].split(", ")
        creatorstring = m[1]
        if len(creators) > 1:
            commacreators = creators[:-1]
            ampersandcreator = creators[-1]
            creatorstring = ", ".join(commacreators) + " & " + ampersandcreator
        print("%s (Forthcoming). %s." % (creatorstring, title))
