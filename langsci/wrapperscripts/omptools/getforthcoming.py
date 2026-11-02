import requests
from bs4 import BeautifulSoup
from langsci.catalog.langscipressorg_webcrawler import get_soup, get_citeinfo

url = "https://langsci-press.org/catalog"
html = requests.get(url).text
soup = BeautifulSoup(html, "html.parser")
books = soup.find_all("div", "obj_monograph_summary")
meta = []

for i in range(300,500):
    soup = get_soup(i)
    citeinfo = get_citeinfo(soup)
    try:
        year = citeinfo["year"]
    except TypeError:
        pass
        # print(i)
    # print(year)
    try:
        if citeinfo["year"].startswith("Forthcoming"):
            print(citeinfo["title"], end=".")
            if "author" in citeinfo:
                print(citeinfo["author"])
            elif "editor" in citeinfo:
                print(f"{citeinfo["editor"]} (ed.)")
        print()
    except TypeError:
        pass
